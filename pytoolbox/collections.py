# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
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

from __future__ import absolute_import, division

import math
from collections import deque
from .datetime import total_seconds

class pygal_deque(deque):
    u"""
    A deque None'ing duplicated values to produce nicer pygal line charts (e.g. 5555322211111 -> 5__532_21___1).

    .. warning::

        Not yet implemented:

        * appendleft(x)
        * clear()
        * count(x)
        * extend(iterable)
        * extendleft(iterable)
        * pop()
        * popleft()
        * remove(value)
        * reverse()
        * rotate(n)
    """

    def append(self, value):
        if not hasattr(self, 'last'):
            self.last = None
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

    def __init__(self, sparse_events_table, time_range, time_speedup, sleep_factor=1.0):
        u"""Scan a spare events table and replace missing entry by previous (non empty) entry."""
        self.time_range, self.time_speedup, self.sleep_factor = time_range, time_speedup, sleep_factor
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

    def sleep_time(self, time, time_speedup=None, sleep_factor=None):
        u"""
        Return required sleep time to wait for next scheduled event.

        **Example usage**

        >>> from nose.tools import assert_equal
        >>> table = EventsTable({0: 'salut'}, 24, 60)
        >>> assert_equal(table.sleep_time(1), 59)
        >>> assert_equal(table.sleep_time(58), 2)
        >>> assert_equal(table.sleep_time(60), 60)
        >>> assert_equal(table.sleep_time(62), 58)
        >>> assert_equal(table.sleep_time(3590, time_speedup=1), 10)
        >>> assert_equal(table.sleep_time(12543, time_speedup=1), 1857)
        >>> assert_equal(table.sleep_time(12543, time_speedup=1, sleep_factor=2), 57)
        >>> assert_equal(table.sleep_time(12600, time_speedup=1, sleep_factor=2), 1800)
        >>> assert_equal(table.sleep_time(1, time_speedup=60, sleep_factor=1), 59)
        >>> assert_equal(table.sleep_time(1, time_speedup=60, sleep_factor=2), 29)
        >>> assert_equal(table.sleep_time(30, time_speedup=60, sleep_factor=2), 30)
        >>> table.time_range = 1
        >>> assert_equal(table.sleep_time(1, time_speedup=1), 149)
        """
        # 150 = 3600 / 24
        d = self.time_range * 150 / ((time_speedup or self.time_speedup) * (sleep_factor or self.sleep_factor))
        return math.ceil(d - (total_seconds(time) % d))
