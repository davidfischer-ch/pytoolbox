# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

from kitchen.text.converters import to_bytes


class ForbiddenError(Exception):
    u"""A forbidden error."""
    pass


def assert_raises_item(exception_cls, something, index, delete=False):
    u"""
    """
    try:
        if delete:
            del something[index]
        else:
            something[index]
        return
    except Exception as e:
        if not isinstance(e, exception_cls):
            raise ValueError(to_bytes(u'Exception {0} is not an instance of {1}.'.format(
                             e.__class__, exception_cls)))
        return
    raise AssertionError(to_bytes(u'Exception {0} not raised.'.format(exception_cls)))
