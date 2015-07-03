# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
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

"""
Module related to parsing arguments from the command-line.

**Example usage**

>>> from nose.tools import eq_
>>> from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
>>> parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog='My super cool software.')
>>> x = parser.add_argument('directory', action=FullPaths, type=is_dir)
>>> print(parser.parse_args(['/usr/lib']).directory)
/usr/lib
>>> eq_(parser.parse_args(['.']).directory, os.path.abspath(os.path.expanduser(os.getcwd())))
>>> parser.parse_args(['/does_not_exist/'])
Traceback (most recent call last):
    ...
SystemExit: 2
"""

import argparse, os
from .encoding import to_bytes

__all__ = ('is_dir', 'is_file', 'FullPaths', 'Range')

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
    """"Return a list with the result of f(value) for value in values."""
    def _multiple(values):
        return [f(v) for v in values] if isinstance(values, (list, tuple)) else f(values)
    return _multiple


class FullPaths(argparse.Action):
    """Expand user/relative paths."""
    def __call__(self, parser, namespace, values, option_string=None):
        fullpath = lambda p: os.path.abspath(os.path.expanduser(p))
        setattr(namespace, self.dest, fullpath(values) if isinstance(values, str) else [fullpath(v) for v in values])


class Range(object):

    def __init__(self, type, min, max):
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
