# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys

from . import module

_all = module.All(globals())


def confirm(question=None, default=False, stream=sys.stdout):
    """
    Return True if user confirm the action, else False. `default` if user only press ENTER.

    **Example usage**

    ::

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
        stream.flush()
        answer = raw_input()  # noqa
        if not answer:
            return default
        if answer.lower() in ('y', 'yes'):
            return True
        elif answer.lower() in ('n', 'no'):
            return False
        stream.write('please enter y(es) or n(o).' + os.linesep)
        stream.flush()


def choice(question='', choices=[], stream=sys.stdout):
    """
    Prompt the user for a choice and return his/her answer.

    **Example of usage**

    ::

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
        ans = raw_input(question)  # noqa
        if ans in choices:
            return ans
        stream.write('Please choose between {1}.{0}'.format(os.linesep, choices_string))


def print_error(message, exit_code=1, stream=sys.stderr):
    """
    Print an error message and exit if `exit_code` is not None.

    **Example usage**

    In following example stream is set to `sys.stdout` and exit is disabled (for :mod:`doctest`):

    >>> print_error(u"It's not a bug - it's an undoc. feature.", exit_code=None, stream=sys.stdout)
    [ERROR] It's not a bug - it's an undoc. feature.
    """
    stream.write('[ERROR] {1}{0}'.format(os.linesep, message))
    stream.flush()
    if exit_code is not None:
        sys.exit(exit_code)

if __name__ == '__main__':

    if confirm('Please confirm this'):
        print('You confirmed')
    else:
        print('You do not like my question')

    print(choice('Select a language', ['Italian', 'French']))


def progress_bar(start_time, current, total, size=50, done='=', todo=' ',
                 template='\r[{done}{todo}]', stream=sys.stdout):
    """
    Show a progress bar. Default `template` string starts with a carriage return to update progress
    on same line.

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


__all__ = _all.diff(globals())
