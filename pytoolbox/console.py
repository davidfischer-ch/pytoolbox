from typing import Optional
import atexit, code, os, sys

__all__ = ['confirm', 'choice', 'print_error', 'progress_bar', 'shell']


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
    question = f"{question} ? [{'Y/n' if default else 'y/N'}]: "
    while True:
        stream.write(question)
        stream.flush()
        answer = input()
        if not answer:
            return default
        if answer.lower() in ('y', 'yes'):
            return True
        if answer.lower() in ('n', 'no'):
            return False
        stream.write(f'please enter y(es) or n(o).{os.linesep}')
        stream.flush()


def choice(question='', choices=tuple(), stream=sys.stdout):
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
        question = f'[{choices_string}]? '
    else:
        question = f'{question} [{choices_string}]: '

    # loop until an acceptable choice has been answered
    while True:
        ans = input(question)
        if ans in choices:
            return ans
        stream.write(f'Please choose between {choices_string}.{os.linesep}')


def print_error(message, exit_code=1, stream=sys.stderr):
    """
    Print an error message and exit if `exit_code` is not None.

    **Example usage**

    In following example stream is set to `sys.stdout` and exit is disabled (for :mod:`doctest`):

    >>> print_error("It's not a bug - it's an undoc. feature.", exit_code=None, stream=sys.stdout)
    [ERROR] It's not a bug - it's an undoc. feature.
    """
    stream.write(f'[ERROR] {message}{os.linesep}')
    stream.flush()
    if exit_code is not None:
        sys.exit(exit_code)


def progress_bar(
    start_time,  # pylint:disable=unused-argument
    current,
    total,
    size=50,
    done='=',
    todo=' ',
    template='\r[{done}{todo}]',
    stream=sys.stdout
):
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


def shell(banner=None, history_filename='~/.python_history', history_length=1000, imported=None):
    """Execute an interactive shell with auto-completion and history (if available)."""
    # Setup auto-completion and file history, credits to @kyouko-taiga!
    try:
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.set_completer(rlcompleter.Completer(imported).complete)
        readline.parse_and_bind("tab:complete")
        history_filename = os.path.abspath(os.path.expanduser(history_filename))
        try:
            readline.read_history_file(history_filename)
            readline.set_history_length(history_length)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, history_filename)
    return code.interact(banner=banner, local=imported)


if __name__ == '__main__':

    if confirm('Please confirm this'):
        print('You confirmed')
    else:
        print('You do not like my question')

    print(choice('Select a language', ['Italian', 'French']))


def toggle_colors(
    env: Optional[dict[str, str]] = None,
    *,
    colorize: bool,
    disable_vars=('NO_COLOR', 'ANSI_COLORS_DISABLED'),
    enable_vars=('FORCE_COLOR', )
) -> dict[str, str]:
    """
    Return `env` (defaulting to `os.environ`) updated to enable or disable colors.

    Reference: https://github.com/termcolor/termcolor/blob/main/src/termcolor/termcolor.py

    **Example usage**

        >> os.environ = toggle_colors(colorize=True)

    Then colors are guaranteed!
    """
    env = {
        k: v for k, v in (env or os.environ).items()
        if k not in disable_vars and k not in enable_vars
    }
    if colorize:
        env[enable_vars[0]] = 'yes'
    else:
        env[disable_vars[0]] = 'yes'
    return env
