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

from __future__ import division

import math
from collections import deque
from py_datetime import total_seconds

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


class EventsTable(object):

    def __init__(self, sparse_events_table, time_range, time_speedup):
        u"""Scan a spare events table and replace missing entry by previous (non empty) entry."""
        self.time_range, self.time_speedup = time_range, time_speedup
        previous_event = sparse_events_table[0]
        self.events = {}
        for index in range(self.time_range):
            event = sparse_events_table.get(index, previous_event)
            self.events[index] = event
            previous_event = event

    def get(self, time, time_speedup=None, default_value=None):
        # u"""
        # >>> from nose.tools import assert_equal
        # >>> def test_get_index(time_range, time_speedup):
        # ...     table = EventsTable({0: 'salut'}, time_range, time_speedup)
        # ...     modulo = previous = 0
        # ...     for t in range(24*3600+1):
        # ...         index = table.get(t+2*60, time_range, time_speedup)[0]
        # ...         if previous > index:
        # ...             modulo += 1
        # ...         assert(0 <= index < time_range)
        # ...         previous = index
        # ...     assert_equal(modulo, time_speedup)

        # Test get_index with a speedup of 1440 (maps 1 minute to 24 hours):
        # >>> test_get_index(24, 24 * 60)

        # Test get_index with a speedup of 12 (maps 2 hours to 24 hours):
        # >>> test_get_index(24, 12)
        # """
        index = int((total_seconds(time) * ((time_speedup or self.time_speedup) / 3600) % self.time_range))
        return index, self.events.get(index, default_value)

    def sleep_time(self, time, time_speedup=None):
        u"""
        >>> from nose.tools import assert_equal
        >>> table = EventsTable({0: 'salut'}, 24, 60)
        >>> assert_equal(table.sleep_time(1), 59)
        >>> assert_equal(table.sleep_time(58), 2)
        >>> assert_equal(table.sleep_time(60), 60)
        >>> assert_equal(table.sleep_time(62), 58)
        >>> assert_equal(table.sleep_time(3590, 1), 10)
        >>> assert_equal(table.sleep_time(12543, 1), 1857)
        >>> table.time_range = 1
        >>> assert_equal(table.sleep_time(1, 1), 149)
        """
        d = self.time_range * 150 / (time_speedup or self.time_speedup)  # 150 = 3600 / 24
        return math.ceil(d - (total_seconds(time) % d))
