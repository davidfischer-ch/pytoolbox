# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

u"""
Module related to parsing arguments from the command-line.

**Example usage**

>>> from nose.tools import eq_
>>> from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
>>> parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=u'My super cool software.')
>>> x = parser.add_argument(u'directory', action=FullPaths, type=is_dir)
>>> print(parser.parse_args([u'/usr/lib']).directory)
/usr/lib
>>> eq_(parser.parse_args([u'.']).directory, os.path.abspath(os.path.expanduser(os.getcwd())))
>>> parser.parse_args([u'/does_not_exist/'])
Traceback (most recent call last):
    ...
SystemExit: 2
"""

import argparse, os
from .encoding import to_bytes

# Credits https://gist.github.com/brantfaircloth/1443543


def is_dir(path):
    u"""
    Check if path is an actual directory and return it.

    Please find a "real world" example in the docstring of this module.

    **Example usage**

    >>> print(is_dir(u'/home'))
    /home
    >>> is_dir(u'sjdsajkd')
    Traceback (most recent call last):
        ...
    ArgumentTypeError: sjdsajkd is not a directory
    """
    if os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(to_bytes(u'{0} is not a directory'.format(path)))


class FullPaths(argparse.Action):
    u"""Expand user- and relative-paths."""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))
