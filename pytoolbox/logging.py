from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, TypeAlias
import logging
import sys

from .collections import merge_dicts

__all__ = [
    'CRITICAL',
    'FATAL',
    'ERROR',
    'WARN',
    'WARNING',
    'INFO',
    'DEBUG',
    'NOTSET',
    'Color',
    'BasicLoggerFunc',
    'BasicFuncLogger',
    'LoggerType',
    'Logger',
    'LogRecord',
    'get_logger',
    'reset_logger',
    'setup_logging',
    'ColorizeFilter'
]

CRITICAL: int = logging.CRITICAL
FATAL: int = logging.FATAL
ERROR: int = logging.ERROR
WARN: int = logging.WARNING
WARNING: int = logging.WARNING
INFO: int = logging.INFO
DEBUG: int = logging.DEBUG
NOTSET: int = logging.NOTSET

# Terminal colors (termcolor)
Color: TypeAlias = Literal[
    'black',
    'grey',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'light_grey',
    'dark_grey',
    'light_red',
    'light_green',
    'light_yellow',
    'light_blue',
    'light_magenta',
    'light_cyan',
    'white'
]


class BasicLoggerFunc(Protocol):  # pylint:disable=too-few-public-methods
    def __call__(self, messsage: str) -> None:
        ...


class BasicFuncLogger(logging.Logger):

    def __init__(self, log_func) -> None:
        self._log_func = log_func
        super().__init__(name=f'{log_func.__module__}.{log_func.__name__}')

    def _log(self, level, msg, *args, **kwargs) -> None:  # pylint:disable=unused-argument
        self._log_func(msg)


LoggerType: TypeAlias = BasicLoggerFunc | logging.Logger | str | None
Logger = logging.Logger
LogRecord = logging.LogRecord


def get_logger(log: LoggerType) -> logging.Logger:
    """Convenient function returning an instance of logger for various use cases."""
    if isinstance(log, Logger):
        return log
    if isinstance(log, str):
        return logging.getLogger(log)
    if hasattr(log, '__call__'):
        return BasicFuncLogger(log_func=log)
    raise NotImplementedError(f'Logging with {log!r} of type {type(log)}')


def reset_logger(log: LoggerType) -> logging.Logger:
    log = get_logger(log)
    log.setLevel(logging.NOTSET)
    log.disabled = False
    log.propagate = True
    log.filters.clear()
    for handler in log.handlers.copy():
        # Copied from `logging.shutdown`
        try:
            handler.acquire()
            handler.flush()
            handler.close()
        except (OSError, ValueError):
            pass
        finally:
            handler.release()
        log.removeHandler(handler)
    return log


def setup_logging(
    log: LoggerType = '',
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
    log = get_logger(log)
    if reset:
        reset_logger(log)
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

    color_by_level: dict[int | str, Color] = {
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
