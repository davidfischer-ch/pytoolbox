from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Literal, overload
import collections
import hashlib
import os
import random
import string

from . import filesystem

__all__ = ['new', 'checksum', 'get_password_generator', 'githash', 'guess_algorithm']


def new(algorithm: Callable | str = hashlib.sha256) -> Callable:
    """
    Return an instance of a hash algorithm from :mod:`hashlib` if `algorithm`
    is a string else instantiate algorithm.
    """
    return hashlib.new(algorithm) if isinstance(algorithm, str) else algorithm()


def checksum(
    path_or_data: Path | str,
    *,
    encoding: str = 'utf-8',
    algorithm: Callable | str = hashlib.sha256,
    chunk_size: int | None = None
) -> str:
    """
    Return the result of hashing `data` by given hash `algorithm`.

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> checksum('')
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    >>> checksum('', algorithm=hashlib.md5)
    'd41d8cd98f00b204e9800998ecf8427e'
    >>> checksum('give me some hash please')
    'cebf462dd7771c78d3957446b1b4a2f5928731ca41eff66aa8817a6513ea1313'
    >>> checksum('et ça fonctionne !\\n')
    'ced3a2b067d105accb9f54c0b37eb79c9ec009a61fee5df7faa8aefdbff1ddef'
    >>> checksum('et ça fonctionne !\\n', algorithm='md5')
    '3ca34e7965fd59beaa13b6e7094f43e7'
    >>> checksum(directory / '..' / 'LICENSE.rst')
    '793b47e008d4261d4fdc5ed24d56eb8d879b9a2e72d37c24a6944558b87909f8'
    >>> checksum(directory / '..' / 'LICENSE.rst', chunk_size=997)
    '793b47e008d4261d4fdc5ed24d56eb8d879b9a2e72d37c24a6944558b87909f8'
    """
    hasher = new(algorithm)
    for data in filesystem.get_bytes(path_or_data, encoding=encoding, chunk_size=chunk_size):
        hasher.update(data)    # type: ignore[attr-defined]
    return hasher.hexdigest()  # type: ignore[attr-defined]


def get_password_generator(
    characters: str = string.ascii_letters + string.digits,
    length: int = 16
) -> collections.defaultdict[str, str]:
    """
    Return a dead simple password generator in the form of a dictionary with
    missing keys generated on the fly.

    **Example usage**

    >>> import re
    >>> passwords = get_password_generator()
    >>> passwords['redis'] = 'some-hardcoded-password'
    >>> passwords['redis']
    'some-hardcoded-password'
    >>> re.match(r'[0-9a-zA-Z]{16}', passwords['db']) is None
    False
    >>> passwords['db'] == passwords['db']
    True
    >>> passwords['cache'] == passwords['db']
    False
    """
    return collections.defaultdict(
        lambda: ''.join(random.SystemRandom().choice(characters) for _ in range(length)))


# TODO implement githash class with interface: hg.python.org/cpython/file/3.4/Lib/hashlib.py
# TODO add length optional argument to implement chunk'ed update()
def githash(
    path_or_data: Path | str,
    *,
    encoding: str = 'utf-8',
    chunk_size: int | None = None
) -> str:
    """
    Return the blob of some data.

    This is how Git `calculates <http://stackoverflow.com/questions/552659>`_
    the SHA1 for a file (or, in Git terms, a "blob")::

        sha1('blob ' + filesize + (the byte 0) + data)

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> githash('')
    'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'
    >>> githash('give me some hash please')
    'abdd1818289725c072eff0f5ce185457679650be'
    >>> githash('et ça fonctionne !\\n')
    '91de5baf6aaa1af4f662aac4383b27937b0e663d'
    >>> githash(directory / '..' / 'LICENSE.rst')
    'b699ab5e129290e7bce9cbbc70443bf1cdede4ea'
    >>> githash(directory / '..' / 'LICENSE.rst', chunk_size=256)
    'b699ab5e129290e7bce9cbbc70443bf1cdede4ea'
    """
    hasher = hashlib.sha1()
    if isinstance(path_or_data, Path):
        hasher.update((f'blob {os.path.getsize(path_or_data)}\0').encode('utf-8'))
        for data_bytes in filesystem.get_bytes(
            path_or_data,
            encoding=encoding,
            chunk_size=chunk_size
        ):
            hasher.update(data_bytes)
    else:
        data_bytes = next(filesystem.get_bytes(
            path_or_data,
            encoding=encoding,
            chunk_size=None
        ))
        hasher.update((f'blob {len(data_bytes)}\0').encode('utf-8'))
        hasher.update(data_bytes)
    return hasher.hexdigest()


@overload
def guess_algorithm(
    checksum_value: str,
    algorithms: Iterable[Callable | str] | None = None,
    *,
    unique: Literal[False] = False
) -> Callable | None:
    ...


@overload
def guess_algorithm(
    checksum_value: str,
    algorithms: Iterable[Callable | str] | None = None,
    *,
    unique: Literal[True]
) -> set[Callable]:
    ...


def guess_algorithm(checksum_value, algorithms=None, *, unique=False):
    """
    Guess the algorithms that have produced the checksum_value, based on its size.

    **Example usage**

    >>> algorithms = ('md5', 'sha256', 'sha512')
    >>> long_checksum = '43d92a466b57e3744532eab7d760708028a7562d9678f6762bf341f29b921e42'
    >>> short_checksum = '2b31de8940dfd3286f70c316f701a54a'
    >>> guess_algorithm('', algorithms)
    set()
    >>> {a.name for a in guess_algorithm(long_checksum, algorithms)}
    {'sha256'}
    >>> guess_algorithm(long_checksum, algorithms, unique=True).name
    'sha256'
    >>> guess_algorithm('toto', algorithms, unique=True) is None
    True

    Following examples depends of your system, so they are disabled::

    >> {a.name for a in guess_algorithm(short_checksum)}
    {'md4', 'md5'}
    >> {a.name for a in guess_algorithm(long_checksum))}
    {'sha256'}
    """
    digest_size = len(checksum_value) / 2
    if algorithms:
        algorithms = [hashlib.new(a) if isinstance(a, str) else a for a in algorithms]
    else:
        try:
            algorithms = [hashlib.new(a) for a in hashlib.algorithms_available if a.lower() == a]
        except AttributeError as ex:
            raise NotImplementedError(
                "Your version of hashlib doesn't implement algorithms_available") from ex
    digest_size_to_algorithms = collections.defaultdict(set)
    for algorithm in algorithms:
        digest_size_to_algorithms[algorithm.digest_size].add(algorithm)
    possible_algorithms = digest_size_to_algorithms[digest_size]
    if unique:
        return possible_algorithms.pop() if len(possible_algorithms) == 1 else None
    return possible_algorithms
