from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO
import atexit
import code
import os
import sys

__all__ = ['confirm', 'choice', 'print_error', 'progress_bar', 'shell', 'toggle_colors']


def confirm(
    question: str = 'Confirm',
    *,
    default: bool = False,
    stream: TextIO = sys.stdout
) -> bool:
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
    question = f"{question} ? [{'Y/n' if default else 'y/N'}]: "
    while True:
        stream.write(question)
        stream.flush()
        if not (answer := input()):  # pylint:disable=bad-builtin
            return default
        if answer.lower() in ('y', 'yes'):  # pylint:disable=use-set-for-membership
            return True
        if answer.lower() in ('n', 'no'):  # pylint:disable=use-set-for-membership
            return False
        stream.write(f'please enter y(es) or n(o).{os.linesep}')
        stream.flush()


def choice(
    question: str = '',
    *,
    choices: tuple[str, ...] | list[str],
    stream: TextIO = sys.stdout
) -> str:
    """
    Prompt the user for a choice and return his/her answer.

    **Example of usage**

    ::

        >> choice('What is your favorite color?', choices=['blue', 'orange', 'red'])
        What is your favourite color? [blue, orange, red]: orange
        orange
        >> choice(choices=['male', 'female'])
        [male, female]? female
        female
    """

    # Generate question and choices list
    choices_string = ', '.join(choices)
    if not question:
        question = f'[{choices_string}]? '
    else:
        question = f'{question} [{choices_string}]: '

    # Loop until an acceptable choice has been answered
    while True:
        if (answer := input(question)) in choices:  # pylint:disable=bad-builtin
            return answer
        stream.write(f'Please choose between {choices_string}.{os.linesep}')


def print_error(message: str, exit_code: int | None = 1, stream: TextIO = sys.stderr) -> None:
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
    *,
    start_time: float,  # pylint:disable=unused-argument
    current: int,
    total: int,
    size: int = 50,
    done: str = '=',
    todo: str = ' ',
    template: str = '\r[{done}{todo}]',
    stream: TextIO = sys.stdout
) -> None:
    """
    Show a progress bar. Default `template` string starts with a carriage return to update progress
    on same line.

    **Example usage**

    >>> import functools
    >>> import time
    >>> progress = functools.partial(progress_bar, template='[{done}{todo}]', stream=sys.stdout)
    >>> progress(start_time=time.time(), current=10, total=15, size=30)
    [====================          ]
    >>> progress(start_time=time.time(), current=1, total=6, size=10)
    [=         ]
    >>> progress(start_time=time.time(), current=3, total=5, size=5, done='+', todo='-')
    [+++--]
    """
    if total:
        progress = int(size * current / total)
        stream.write(template.format(done=done * progress, todo=todo * (size - progress)))
        stream.flush()


def shell(
    banner: str | None = None,
    *,
    history_filename: Path = Path('~/.python_history'),
    history_length: int = 1000,
    imported: dict[str, Any] | None = None
) -> None:
    """Execute an interactive shell with auto-completion and history (if available)."""
    # Setup auto-completion and file history, credits to @kyouko-taiga!
    history_filename = history_filename.expanduser().resolve()
    try:
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.set_completer(rlcompleter.Completer(imported).complete)
        readline.parse_and_bind("tab:complete")
        try:
            readline.read_history_file(history_filename)
            readline.set_history_length(history_length)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, history_filename)
    code.interact(banner=banner, local=imported)


def toggle_colors(
    env: dict[str, str] | None = None,
    *,
    colorize: bool,
    disable_vars: tuple[str, ...] | list[str] = ('NO_COLOR', 'ANSI_COLORS_DISABLED'),
    enable_vars: tuple[str, ...] | list[str] = ('FORCE_COLOR', )
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
