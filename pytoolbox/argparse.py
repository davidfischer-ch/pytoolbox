# -*- encoding: utf-8 -*-

"""
Module related to parsing arguments from the command-line.

**Example usage**

>>> import argparse
>>> from pytoolbox.unittest import asserts
>>> parser = argparse.ArgumentParser(
...     formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog='My super cool software.'
... )
>>> x = parser.add_argument('directory', action=FullPaths, type=is_dir)
>>> print(parser.parse_args(['/usr/lib']).directory)
/usr/lib
>>> asserts.equal(
...     parser.parse_args(['.']).directory, os.path.abspath(os.path.expanduser(os.getcwd())))
>>> parser.parse_args(['/does_not_exist/'])
Traceback (most recent call last):
    ...
SystemExit: 2
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse, getpass, os, shutil

from . import itertools, module
from .encoding import to_bytes

_all = module.All(globals())

# Credits https://gist.github.com/brantfaircloth/1443543


def is_dir(path):
    """Check if `path` is an actual directory and return it."""
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(to_bytes('{0} is not a directory'.format(path)))


def is_file(path):
    """Check if `path` is an actual file and return it."""
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(to_bytes('{0} is not a file'.format(path)))


def multiple(f):
    """Return a list with the result of `f`(value) for value in values."""
    def _multiple(values):
        return [f(v) for v in values] if isinstance(values, (list, tuple)) else f(values)
    return _multiple


def password(value):
    return value or getpass.getpass('Password: ')


def set_columns(value=None, default=120):
    if value is None:
        try:
            value = shutil.get_terminal_size().columns
        except AttributeError:
            value = default
    os.environ['COLUMNS'] = str(value)


class FullPaths(argparse.Action):
    """Expand user/relative paths."""
    def __call__(self, parser, namespace, values, option_string=None):
        fullpath = lambda p: os.path.abspath(os.path.expanduser(p))
        setattr(namespace, self.dest, itertools.extract_single(
            list(fullpath(v) for v in itertools.chain(values))))


class Range(object):

    def __init__(self, type, min, max):  # pylint:disable=redefined-builtin
        self.type = type
        self.min = min
        self.max = max

    def __call__(self, value):
        try:
            value = self.type(value)
        except:
            raise argparse.ArgumentTypeError('Must be of type {0.type.__name__}'.format(self))
        if not (self.min <= value <= self.max):
            raise argparse.ArgumentTypeError('Must be in range [{0.min}, {0.max}]'.format(self))
        return value


class HelpArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        set_columns(kwargs.pop('columns', None))
        super(HelpArgumentParser, self).__init__(*args, formatter_class=HelpFormatter, **kwargs)


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


__all__ = _all.diff(globals())
