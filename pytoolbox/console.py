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

__all__ = ('confirm', 'choice', 'print_error', 'progress_bar')


def confirm(question=None, default=False, stream=sys.stdout):
    """
    Return True if user confirm the action, else False. `default` if user only press ENTER.

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
        stream.write(question)
        answer = raw_input()
        if not answer:
            return default
        if answer.lower() in ('y', 'yes'):
            return True
        elif answer.lower() in ('n', 'no'):
            return False
        stream.write('please enter y(es) or n(o).\n')


def choice(question='', choices=[], stream=sys.stdout):
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
        stream.write('Please choose between {0}.\n'.format(choices_string))


def print_error(message, exit_code=1, stream=sys.stderr):
    """
    Print a error message and exit if `exit_code` is not None.

    **Example usage**

    In following example stream is set to `stdout` and exit is disabled (for :mod:`doctest`):

    >>> print_error(u"It's not a bug - it's an undocumented feature.", exit_code=None, stream=sys.stdout)
    [ERROR] It's not a bug - it's an undocumented feature.
    """
    stream.write('[ERROR] {0}\n'.format(message))
    if exit_code is not None:
        sys.exit(exit_code)

if __name__ == '__main__':

    if confirm('Please confirm this'):
        print('You confirmed')
    else:
        print('You do not like my question')

    print(choice('Select a language', ['Italian', 'French']))


def progress_bar(start_time, current, total, size=50, done='=', todo=' ', template='\r[{done}{todo}]',
                 stream=sys.stdout):
    """
    Show a progress bar. Default template string starts with a carriage return to update progress on same line.

    **Example usage**

    >>> import functools, time
    >>> progress = functools.partial(progress_bar, template='[{done}{todo}]', stream=sys.stdout)

    >>> progress(time.time(), 10, 15, size=30)
    [====================          ]

    >>> progress(time.time(), 1, 6, size=10)
    [=         ]

    >>> progress(time.time(), 3, 5, size=5, done='+', todo='-')
    [+++--]
    """
    if total:
        progress = int(size * current / total)
        stream.write(template.format(done=done * progress, todo=todo * (size - progress)))
        stream.flush()
