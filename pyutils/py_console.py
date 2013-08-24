#!/usr/bin/env python
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

from __future__ import print_function

import sys


def confirm(question=None, default=False):
    u"""
    Return True if user confirm the action, else False. ``default`` if user only press ENTER.

    >> confirm(u'Do it now', default=True)
    Do it now ? [Y/n]: 
    True
    >> confirm(u'Are you sure', default=False)
    Are you sure ? [y/N]: 
    False
    >> confirm(u'Really, I am sure that is false', default=False)
    Really, I am sure that is false ? [y/N]: y
    True
    """
    if question is None:
        question = u'Confirm'
    question = u'{0} ? [{1}]: '.format(question, u'Y/n' if default else u'y/N')
    while True:
        ans = raw_input(question)
        if not ans:
            return default
        if ans in (u'y', u'Y'):
            return True
        elif ans in (u'n', u'N'):
            return False
        print(u'please enter y or n.')


def print_error(message, output=sys.stderr, exit_code=1):
    u"""
    Print a error message and exit if ``exit_code`` is not None.

    **Example usage**:

    In following example output is set to stdout and exit is disabled (for doctest):

    >>> print_error(u"It's not a bug - it's an undocumented feature.", output=sys.stdout, exit_code=None)
    [ERROR] It's not a bug - it's an undocumented feature.
    """
    print(u'[ERROR] {0}'.format(message), file=output)
    if exit_code is not None:
        sys.exit(exit_code)