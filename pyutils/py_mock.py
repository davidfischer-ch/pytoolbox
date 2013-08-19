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

from six import PY3

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

        import pyutils.py_mock
        pyutils.py_mock.MOCK_SIDE_EFFECT_RETURNS = [u'1st', {u'title': u'2nd'}, EOFError(u'last')]

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
