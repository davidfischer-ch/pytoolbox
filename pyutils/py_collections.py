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

from collections import deque

class pygal_deque(deque):
    u"""
    A deque None'ing duplicated values to produce nicer pygal line charts (e.g. 5555322211111 -> 5__532_21___1).

    .. warning::

        Not yet implemented :
        appendleft(x)
        clear()
        count(x)
        extend(iterable)
        extendleft(iterable)
        pop()
        popleft()
        remove(value)
        reverse()
        rotate(n)
    """

    def __init__(self, **kwargs):
        super(pygal_deque, self).__init__(**kwargs)
        self.last = None

    def append(self, value):
        if value != self.last and value is not None:
            try:
                self[-1] = self.last
            except:
                pass
            self.last = value
        else:
            value = None
        try:
            first = self[0]
        except IndexError:
            first = None
        super(pygal_deque, self).append(value)
        if self[0] is None:
            self[0] = first

    @property
    def list(self):
        self_list = list(self)
        try:
            if self.last is not None:
                self_list[-1] = self.last
        except:
            pass
        return self_list
