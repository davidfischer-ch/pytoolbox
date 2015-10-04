# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import logging, sys

from termcolor import colored

from . import module

_all = module.All(globals())


def setup_logging(name='', reset=False, path=None, console=False, level=logging.DEBUG,
                  fmt='%(asctime)s %(levelname)-8s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S'):
    """
    Setup logging (TODO).

    :param name: TODO
    :type name: str
    :param reset: Unregister all previously registered handlers ?
    :type reset: bool
    :param path: TODO
    :type name: str
    :param console: Toggle console output (stdout)
    :type console: bool
    :param level: TODO
    :type level: int
    :param fmt: TODO
    :type fmt: str
    :param datefmt: TODO
    :type datefmt: str

    **Example usage**

    Setup a console output for logger with name *test*:

    >>> setup_logging(name='test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log = logging.getLogger('test')
    >>> log.info('this is my info')
    this is my info
    >>> log.debug('this is my debug')
    this is my debug
    >>> log.setLevel(logging.INFO)
    >>> log.debug('this is my hidden debug')
    >>> log.handlers = []  # Remove handlers manually: pas de bras, pas de chocolat !
    >>> log.debug('no handlers, no messages ;-)')

    Show how to reset handlers of the logger to avoid duplicated messages (e.g. in doctest):

    >>> setup_logging(name='test', console=True, fmt=None, datefmt=None)
    >>> setup_logging(name='test', console=True, fmt=None, datefmt=None)
    >>> log.info('double message, tu radote pépé')
    double message, tu radote pépé
    double message, tu radote pépé
    >>> setup_logging(name='test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info('single message')
    single message
    """
    if reset:
        logging.getLogger(name).handlers = []
    if path:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
    if console:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)


class ColorizeFilter(logging.Filter):

    color_by_level = {
        logging.DEBUG: 'yellow',
        logging.ERROR: 'red',
        logging.INFO: 'white'
    }

    def filter(self, record):
        record.raw_msg = record.msg
        color = self.color_by_level.get(record.levelno)
        if color:
            record.msg = colored(record.msg, color)
        return True

__all__ = _all.diff(globals())
