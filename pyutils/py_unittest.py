# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import nose, os
from os.path import abspath, dirname
from six import PY3
from unittest import TestCase

if PY3:
    from unittest.mock import Mock
else:
    from mock import Mock


MOCK_SIDE_EFFECT_RETURNS = [Exception(u'you must set MOCK_SIDE_EFFECT_RETURNS'), {u'title': u'2nd'}]


def mock_cmd(stdout=u'', stderr=u'', returncode=0):
    return Mock(return_value={u'stdout': stdout, u'stderr': stderr, u'returncode': returncode})


def mock_side_effect(*args, **kwargs):
    u"""
    Pop and return values from MOCK_SIDE_EFFECT_RETURNS.

    from your own module, you need to set MOCK_SIDE_EFFECT_RETURNS before using this method::

        import pyutils.py_unittest
        pyutils.py_unittest.MOCK_SIDE_EFFECT_RETURNS = [u'1st', {u'title': u'2nd'}, EOFError(u'last')]

    **example usage**:

    Set content (only required for this doctest, see previous remark):

    Pops return values with ``mock_side_effect``:

    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    Exception: you must set MOCK_SIDE_EFFECT_RETURNS
    >>> print(mock_side_effect())
    {u'title': u'2nd'}
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


def runtests(test_file, cover_packages, packages, ignore=None):
    u"""Run tests and report coverage with nose and coverage."""

    from py_unicode import configure_unicode
    configure_unicode()

    cover_packages = [u'--cover-package={0}'.format(package) for package in cover_packages]
    nose_options = filter(None, [test_file, u'--with-doctest', u'--with-coverage', u'--cover-erase', u'--exe'] +
                          cover_packages + [u'--cover-html', u'-vv', dirname(test_file)] + packages)
    if ignore:
        nose_options += ['-I', ignore]
    os.chdir(abspath(dirname(test_file)))
    return PseudoTestCase(nose.run(argv=nose_options))
