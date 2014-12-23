# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, hashlib
from os.path import getsize

from .encoding import string_types
from .filesystem import get_bytes

__all__ = ('checksum', 'githash', 'guess_algorithm', 'new')


def new(algorithm=hashlib.sha256):
    """
    Return an instance of a hash algorithm from :mod:`hashlib` if `algorithm` is a string else instantiate algorithm.
    """
    return hashlib.new(algorithm) if isinstance(algorithm, string_types) else algorithm()


def checksum(filename_or_data, encoding='utf-8', is_filename=False, algorithm=hashlib.sha256, chunk_size=None):
    """
    Return the result of hashing ``data`` by given hash ``algorithm``.

    **Example usage**

    >>> print(checksum(''))
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    >>> print(checksum('', algorithm=hashlib.md5))
    d41d8cd98f00b204e9800998ecf8427e
    >>> print(checksum('give me some hash please'))
    cebf462dd7771c78d3957446b1b4a2f5928731ca41eff66aa8817a6513ea1313
    >>> print(checksum('et ça fonctionne !\\n'))
    ced3a2b067d105accb9f54c0b37eb79c9ec009a61fee5df7faa8aefdbff1ddef
    >>> print(checksum('et ça fonctionne !\\n', algorithm='md5'))
    3ca34e7965fd59beaa13b6e7094f43e7
    >>> print(checksum('small.mp4', is_filename=True))
    1d720916a831c45454925dea707d477bdd2368bc48f3715bb5464c2707ba9859
    >>> print(checksum('small.mp4', is_filename=True, chunk_size=1024))
    1d720916a831c45454925dea707d477bdd2368bc48f3715bb5464c2707ba9859
    """
    hasher = new(algorithm)
    for data in get_bytes(filename_or_data, encoding, is_filename, chunk_size):
        hasher.update(data)
    return hasher.hexdigest()


def githash(filename_or_data, encoding='utf-8', is_filename=False, chunk_size=None):
    """
    Return the blob of some data.

    This is how Git calculates the SHA1 for a file (or, in Git terms, a "blob")::

        sha1('blob ' + filesize + '\0' + data)

    .. seealso::

        http://stackoverflow.com/questions/552659/assigning-git-sha1s-without-git

    **Example usage**

    >>> print(githash(''))
    e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
    >>> print(githash('give me some hash please'))
    abdd1818289725c072eff0f5ce185457679650be
    >>> print(githash('et ça fonctionne !\\n'))
    91de5baf6aaa1af4f662aac4383b27937b0e663d
    >>> print(githash('small.mp4', is_filename=True))
    1fc478842f51e7519866f474a02ad605235bc6a6
    >>> print(githash('small.mp4', is_filename=True, chunk_size=1024))
    1fc478842f51e7519866f474a02ad605235bc6a6
    """
    s = hashlib.sha1()
    if is_filename:
        s.update(('blob %d\0' % getsize(filename_or_data)).encode('utf-8'))
        for data_bytes in get_bytes(filename_or_data, encoding, is_filename, chunk_size):
            s.update(data_bytes)
    else:
        data_bytes = next(get_bytes(filename_or_data, encoding, is_filename, chunk_size=None))
        s.update(('blob %d\0' % len(data_bytes)).encode('utf-8'))
        s.update(data_bytes)
    return s.hexdigest()


def guess_algorithm(checksum, algorithms=None, unique=False):
    """
    Guess the algorithms that have produced the checksum, based on its size.

    **Example usage**

    >>> from nose.tools import eq_
    >>> algorithms = ('md4', 'md5', 'sha256', 'sha512', 'whirlpool')
    >>> long_checksum = '43d92a466b57e3744532eab7d760708028a7562d9678f6762bf341f29b921e42'
    >>> short_checksum = '2b31de8940dfd3286f70c316f701a54a'

    >>> eq_(guess_algorithm('', algorithms), set())
    >>> eq_(set(a.name for a in guess_algorithm(long_checksum, algorithms)), {'sha256'})
    >>> print(guess_algorithm(long_checksum, algorithms, unique=True).name)
    sha256
    >>> print(guess_algorithm(short_checksum, algorithms, unique=True))
    None

    Following examples depends of your system, so they are disabled:
    >> eq_(set(a.name for a in guess_algorithm(short_checksum)), {'md4', 'md5'})
    >> eq_(set(a.name for a in guess_algorithm(long_checksum)), {'sha256'})
    """
    digest_size = len(checksum) / 2
    if algorithms:
        algorithms = [hashlib.new(a) if isinstance(a, string_types) else a for a in algorithms]
    else:
        try:
            algorithms = [hashlib.new(a) for a in hashlib.algorithms_available if a.lower() == a]
        except AttributeError:
            raise NotImplementedError("Your version of hashlib doesn't implement algorithms_available")
    digest_size_to_algorithms = collections.defaultdict(set)
    for algorithm in algorithms:
        digest_size_to_algorithms[algorithm.digest_size].add(algorithm)
    possible_algorithms = digest_size_to_algorithms[digest_size]
    if unique:
        return possible_algorithms.pop() if len(possible_algorithms) == 1 else None
    return possible_algorithms
