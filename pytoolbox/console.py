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

import sys

__all__ = ('confirm', 'choice', 'print_error')


def confirm(question=None, default=False):
    """
    Return True if user confirm the action, else False. ``default`` if user only press ENTER.

    **Example usage**

    >> confirm('Do it now', default=True)
    Do it now ? [Y/n]:
    True
    >> confirm('Are you sure', default=False)
    Are you sure ? [y/N]:
    False
    >> confirm('Really, I am sure that is false', default=False)
    Really, I am sure that is false ? [y/N]: y
    True
    """
    if question is None:
        question = 'Confirm'
    question = '{0} ? [{1}]: '.format(question, 'Y/n' if default else 'y/N')
    while True:
        ans = raw_input(question)
        if not ans:
            return default
        if ans in ('y', 'Y'):
            return True
        elif ans in ('n', 'N'):
            return False
        print('please enter y or n.')


def choice(question='', choices=[]):
    """
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
    choices_string = ', '.join(choices)
    if question is None:
        question = '[{0}]? '.format(choices_string)
    else:
        question = '{0} [{1}]: '.format(question, choices_string)

    # loop until an acceptable choice has been answered
    while True:
        ans = raw_input(question)
        if ans in choices:
            return ans
        print('Please choose between {0}.'.format(choices_string))


def print_error(message, output=sys.stderr, exit_code=1):
    """
    Print a error message and exit if ``exit_code`` is not None.

    **Example usage**

    In following example output is set to ``stdout`` and exit is disabled (for :mod:`doctest`):

    >>> print_error(u"It's not a bug - it's an undocumented feature.", output=sys.stdout, exit_code=None)
    [ERROR] It's not a bug - it's an undocumented feature.
    """
    print('[ERROR] {0}'.format(message), file=output)
    if exit_code is not None:
        sys.exit(exit_code)

if __name__ == '__main__':

    if confirm('Please confirm this'):
        print('You confirmed')
    else:
        print('You do not like my question')

    print(choice('Select a language', ['Italian', 'French']))
