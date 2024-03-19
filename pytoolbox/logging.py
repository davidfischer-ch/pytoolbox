from __future__ import annotations

from pathlib import Path
from typing import Literal
import logging
import sys

from .collections import merge_dicts

__all__ = ['setup_logging', 'ColorizeFilter']


def setup_logging(
    name_or_log: str | logging.Logger = '',
    reset: bool = False,
    path: Path | str | None = None,
    console: bool = False,
    level: int | str = logging.DEBUG,
    colorize: bool = False,
    color_by_level: dict[int | str, str] | None = None,
    fmt: str = '%(asctime)s %(levelname)-8s - %(message)s',
    datefmt: str = '%d/%m/%Y %H:%M:%S'
) -> logging.Logger:
    """
    Setup logging.

    **Example usage**

    Setup a console output for logger with name *test*:

    >>> log = setup_logging('a', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('this is my info')
    this is my info
    >>> log.debug('this is my debug')
    this is my debug
    >>> log.setLevel(logging.INFO)
    >>> log.debug('this is my hidden debug')
    >>> log.handlers = []  # Remove handlers manually: pas de bras, pas de chocolat !
    >>> log.info('no handlers, no messages ;-)')

    Colorization is not guaranteed (your environment may disable it).
    Use `pytoolbox.console.toggle_colors` appropriately to ensure it.

    Colorize (test is disabled because pytest disable colored outputs):

    >> log = setup_logging('foo', console=True, colorize=True, fmt='%(levelname)-8s - %(message)s')
    >> log.warning('Attention please!')
    WARNING  - \x1b[33mAttention please!\x1b[0m

    Show how to reset handlers of the logger to avoid duplicated messages (e.g. in doctest):

    >>> log = setup_logging('test', console=True, fmt=None, datefmt=None)
    >>> log = setup_logging('test', console=True, fmt=None, datefmt=None)
    >>> log.info('double message, tu radote pépé')
    double message, tu radote pépé
    double message, tu radote pépé

    Resetting works as expected:

    >>> _ = setup_logging('test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('single message')
    single message

    Logging to a file instead:

    >>> import os
    >>> import tempfile
    >>>
    >>> with tempfile.NamedTemporaryFile('r') as f:
    ...     log = setup_logging('my-logger', path=f.name)
    ...     log.info('Ceci va probablement jamais être lu!')
    ...     lines = f.read().split(os.linesep)
    ...
    >>> assert 'INFO     - Ceci va probablement jamais être lu!' in lines[0]
    """
    log = logging.getLogger(name_or_log) if isinstance(name_or_log, str) else name_or_log
    if reset:
        log.handlers = []
    log.setLevel(level)
    if colorize:
        log.addFilter(ColorizeFilter(color_by_level=color_by_level))
    if path:
        file_handler = logging.FileHandler(path)
        file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(file_handler)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(console_handler)
    return log


class ColorizeFilter(logging.Filter):  # pylint:disable=too-few-public-methods

    color_by_level: dict[int | str, str] = {
        logging.DEBUG: 'cyan',
        logging.ERROR: 'red',
        logging.INFO: 'white',
        logging.WARNING: 'yellow'
    }

    def __init__(self, *args, **kwargs) -> None:
        self.color_by_level = merge_dicts(
            self.color_by_level,
            kwargs.pop('color_by_level', None) or {})
        super().__init__(*args, **kwargs)

    def filter(self, record) -> Literal[True]:
        record.raw_msg = record.msg
        if color := self.color_by_level.get(record.levelno):
            import termcolor
            record.msg = termcolor.colored(record.msg, color)
        return True
