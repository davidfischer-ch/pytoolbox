# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

from __future__ import absolute_import

import nose, os, sys
from os.path import abspath, dirname
from unittest import TestCase

if sys.version_info[0] > 2:
    from unittest.mock import Mock
else:
    from mock import Mock


MOCK_SIDE_EFFECT_RETURNS = [Exception(u'you must set MOCK_SIDE_EFFECT_RETURNS'), {u'title': u'2nd'}]


def mock_cmd(stdout=u'', stderr=u'', returncode=0):
    return Mock(return_value={u'stdout': stdout, u'stderr': stderr, u'returncode': returncode})


def mock_side_effect(*args, **kwargs):
    u"""
    Pop and return values from MOCK_SIDE_EFFECT_RETURNS.

    From your own module, you need to set MOCK_SIDE_EFFECT_RETURNS before using this method::

        import pytoolbox.unittest
        pytoolbox.unittest.MOCK_SIDE_EFFECT_RETURNS = [u'1st', {u'title': u'2nd'}, EOFError(u'last')]

    **example usage**:

    Set content (only required for this doctest, see previous remark):

    Pops return values with ``mock_side_effect``:

    >>> from nose.tools import assert_equal
    >>>
    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    Exception: you must set MOCK_SIDE_EFFECT_RETURNS
    >>> assert_equal(mock_side_effect(), {u'title': u'2nd'})
    >>>
    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    IndexError: pop from empty list
    """
    global MOCK_SIDE_EFFECT_RETURNS
    result = MOCK_SIDE_EFFECT_RETURNS.pop(0)
    if isinstance(result, Exception):
        raise result
    return result


class PseudoTestCase(TestCase):
    u"""
    Pseudo test-case to map result from :mod:`nose` to :mod:`unittest`.

    In fact, :mod:`unittest` ``loader.py`` check if we return an instance of TestCase ...
    """

    def __init__(self, result):
        self.result = result

    def __call__(self, something):
        assert(self.result)


def runtests(test_file, cover_packages, packages, ignore=None, extra_options=None):
    u"""Run tests and report coverage with nose and coverage."""
    from .encoding import configure_unicode
    configure_unicode()
    extra_options = extra_options or []
    cover_packages = [u'--cover-package={0}'.format(package) for package in cover_packages]
    nose_options = filter(None, [test_file, u'--with-doctest', u'--with-coverage', u'--cover-erase', u'--exe'] +
                          cover_packages + [u'--cover-html', u'-vv', u'-w', dirname(test_file)] + packages + extra_options)
    if ignore:
        nose_options += ['-I', ignore]
    os.chdir(abspath(dirname(test_file)))
    return PseudoTestCase(nose.run(argv=nose_options))
