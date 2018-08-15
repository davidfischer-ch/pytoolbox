# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import logging, sys

from . import module
from .collections import merge_dicts
from .encoding import string_types

_all = module.All(globals())


def setup_logging(name_or_log='', reset=False, path=None, console=False, level=logging.DEBUG,
                  colorize=False, color_by_level=None,
                  fmt='%(asctime)s %(levelname)-8s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S'):
    """
    Setup logging (TODO).

    :param name_or_log: TODO
    :param reset: Unregister all previously registered handlers ?
    :type reset: bool
    :param path: TODO
    :type name: str
    :param console: Toggle console output (stdout)
    :type console: bool
    :param level: TODO
    :type level: int
    :param colorize: TODO
    :type colorize: bool
    :param color_by_level: TODO
    :type color_by_level: dict
    :param fmt: TODO
    :type fmt: str
    :param datefmt: TODO
    :type datefmt: str

    **Example usage**

    Setup a console output for logger with name *test*:

    >>> log = setup_logging('test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('this is my info')
    this is my info
    >>> log.debug('this is my debug')
    this is my debug
    >>> log.setLevel(logging.INFO)
    >>> log.debug('this is my hidden debug')
    >>> log.handlers = []  # Remove handlers manually: pas de bras, pas de chocolat !
    >>> log.debug('no handlers, no messages ;-)')

    Show how to reset handlers of the logger to avoid duplicated messages (e.g. in doctest):

    >>> _ = setup_logging('test', console=True, fmt=None, datefmt=None)
    >>> _ = setup_logging('test', console=True, fmt=None, datefmt=None)
    >>> log.info('double message, tu radote pépé')
    double message, tu radote pépé
    double message, tu radote pépé
    >>> _ = setup_logging('test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('single message')
    single message
    """
    log = logging.getLogger(name_or_log) if isinstance(name_or_log, string_types) else name_or_log
    if reset:
        log.handlers = []
    log.setLevel(level)
    if colorize:
        log.addFilter(ColorizeFilter())
    if path:
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
    if console:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
    return log


class ColorizeFilter(logging.Filter):

    color_by_level = {
        logging.DEBUG: 'cyan',
        logging.ERROR: 'red',
        logging.INFO: 'white',
        logging.WARNING: 'yellow'
    }

    def __init__(self, *args, **kwargs):
        self.color_by_level = merge_dicts(
            self.color_by_level, kwargs.pop('color_by_level', None) or {})
        super(ColorizeFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        record.raw_msg = record.msg
        color = self.color_by_level.get(record.levelno)
        if color:
            import termcolor
            record.msg = termcolor.colored(record.msg, color)
        return True


__all__ = _all.diff(globals())
