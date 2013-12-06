#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
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

from __future__ import absolute_import, division, print_function, unicode_literals

import sys


def confirm(question=None, default=False):
    u"""
    Return True if user confirm the action, else False. ``default`` if user only press ENTER.

    **Example usage**

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


def choice(question=u'', choices=[]):
    u"""
    Prompt the user for a choice and return his/her answer.
    
    **Example of usage**
    
    >> choice('What is your favorite color?', ['blue', 'orange', 'red'])
    What is your favourite color? [blue, orange, red]: orange
    orange
    >> choice(['male', 'female'])
    [male, female]? female
    female
    """

    # generate question and choices list
    choices_string = u', '.join(choices)
    if question is None:
        question = u'[{0}]? '.format(choices_string)
    else:
        question = u'{0} [{1}]: '.format(question, choices_string)

    # loop until an acceptable choice has been answered
    while True:
        ans = raw_input(question)
        if ans in choices:
            return ans
        print(u'Please choose between {0}.'.format(choices_string))


def print_error(message, output=sys.stderr, exit_code=1):
    u"""
    Print a error message and exit if ``exit_code`` is not None.

    **Example usage**

    In following example output is set to ``stdout`` and exit is disabled (for :mod:`doctest`):

    >>> print_error(u"It's not a bug - it's an undocumented feature.", output=sys.stdout, exit_code=None)
    [ERROR] It's not a bug - it's an undocumented feature.
    """
    print(u'[ERROR] {0}'.format(message), file=output)
    if exit_code is not None:
        sys.exit(exit_code)

if __name__ == u'__main__':

    if confirm('Please confirm this'):
        print(u'You confirmed')
    else:
        print(u'You do not like my question')

    print(choice(u'Select a language', [u'Italian', u'French']))
