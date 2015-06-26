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

import collections, math

from .datetime import total_seconds
from .encoding import string_types

__all__ = ('flatten_dict', 'swap_dict_of_values', 'pygal_deque', 'window', 'EventsTable')


def flatten_dict(the_dict, key_template='{0}.{1}'):
    """
    Flatten the keys of a nested dictionary.

    **Example usage**

    >>> from nose.tools import eq_
    >>> eq_(flatten_dict({'a': 'b', 'c': 'd'}), {'a': 'b', 'c': 'd'})
    >>> eq_(flatten_dict({'a': {'b': {'c': ['d', 'e']}, 'f': 'g'}}), {'a.b.c': ['d', 'e'], 'a.f': 'g'})
    >>> eq_(flatten_dict({'a': {'b': {'c': ['d', 'e']}, 'f': 'g'}}, '{1}-{0}'), {'c-b-a': ['d', 'e'], 'f-a': 'g'})
    """
    def expand_item(key, value):
        if isinstance(value, dict):
            return [(key_template.format(key, k), v) for k, v in flatten_dict(value, key_template).items()]
        else:
            return [(key, value)]
    return dict(item for k, v in the_dict.items() for item in expand_item(k, v))


def swap_dict_of_values(the_dict, type=set, method=set.add):
    """
    Return a dictionary (:class:`collections.defaultdict`) with keys and values swapped.

    This algorithm expect that the values are a container with objects, not a single object.

    **Example usage**

    >>> from nose.tools import eq_
    >>> swap_dict_of_values({'odd': [1, 3], 'even': (0, 2), 'fib': {1, 2, 3}}, type=list, method=list.append)
    defaultdict(<class 'list'>, {0: ['even'], 1: ['odd', 'fib'], 2: ['even', 'fib'], 3: ['odd', 'fib']})
    >>> eq_(swap_dict_of_values({'odd': [1, 3], 'even': (0, 2), 'fib': {1, 2, 3}}, method='add')[2], {'even', 'fib'})
    >>> eq_(swap_dict_of_values({'bad': 'ab', 'example': 'ab'})['a'], {'bad', 'example'})
    """
    method = getattr(type, method) if isinstance(method, string_types) else method
    reversed_dict = collections.defaultdict(type)
    for key, values in the_dict.items():
        for value in values:
            method(reversed_dict[value], key)
    return reversed_dict


class pygal_deque(collections.deque):
    """
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

    def list(self, fill=False):
        self_list = list(self)
        try:
            if self.last is not None:
                self_list[-1] = self.last
        except:
            pass
        if fill and self_list:
            previous = None
            for i in xrange(len(self_list)):
                if self_list[i] is None:
                    self_list[i] = previous
                else:
                    previous = self_list[i]
        return self_list


def window(values, index, delta):
    """
    >>> from nose.tools import eq_
    >>> eq_(window(['a'], 0, 2), (['a'], 0, 0))
    >>> eq_(window(['a', 'b', 'c', 'd'], 2, 0), (['c'], 2, 2))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 0, 1), (['a', 'b', 'c'], 0, 2))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 1, 1), (['a', 'b', 'c'], 0, 2))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 2, 1), (['b', 'c', 'd'], 1, 3))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 3, 1), (['c', 'd', 'e'], 2, 4))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 4, 1), (['c', 'd', 'e'], 2, 4))
    >>> eq_(window(['a', 'b', 'c', 'd', 'e'], 3, 6), (['a', 'b', 'c', 'd', 'e'], 0, 4))
    >>> eq_(window(range(20), 6, 6), ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 0, 12))
    >>> eq_(window(range(20), 7, 6), ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 1, 13))
    >>> eq_(window(range(20), 10, 6), ([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 4, 16))
    >>> eq_(window(range(20), 19, 6), ([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 7, 19))
    """
    length = len(values)
    left, right = index - delta, index + delta
    if left < 0:
        left, right = 0, right - left
    elif right >= length:
        left, right = left - right + length - 1, length - 1
    left, right = max(left, 0), min(right, length - 1)
    return values[left:right + 1], left, right


class EventsTable(object):

    def __init__(self, sparse_events_table, time_range, time_speedup, sleep_factor=1.0):
        """Scan a spare events table and replace missing entry by previous (non empty) entry."""
        self.time_range, self.time_speedup, self.sleep_factor = time_range, time_speedup, sleep_factor
        previous_event = sparse_events_table[0]
        self.events = {}
        for index in xrange(self.time_range):
            event = sparse_events_table.get(index, previous_event)
            self.events[index] = event
            previous_event = event

    def get(self, time, time_speedup=None, default_value=None):
        # u"""
        # >>> from nose.tools import eq_
        # >>> def test_get_index(time_range, time_speedup):
        # ...     table = EventsTable({0: 'salut'}, time_range, time_speedup)
        # ...     modulo = previous = 0
        # ...     for t in xrange(24*3600+1):
        # ...         index = table.get(t+2*60, time_range, time_speedup)[0]
        # ...         if previous > index:
        # ...             modulo += 1
        # ...         assert(0 <= index < time_range)
        # ...         previous = index
        # ...     eq_(modulo, time_speedup)

        # Test get_index with a speedup of 1440 (maps 1 minute to 24 hours):
        # >>> test_get_index(24, 24 * 60)

        # Test get_index with a speedup of 12 (maps 2 hours to 24 hours):
        # >>> test_get_index(24, 12)
        # """
        index = int((total_seconds(time) * ((time_speedup or self.time_speedup) / 3600) % self.time_range))
        return index, self.events.get(index, default_value)

    def sleep_time(self, time, time_speedup=None, sleep_factor=None):
        """
        Return required sleep time to wait for next scheduled event.

        **Example usage**

        >>> from nose.tools import eq_
        >>> table = EventsTable({0: 'salut'}, 24, 60)
        >>> eq_(table.sleep_time(1), 59)
        >>> eq_(table.sleep_time(58), 2)
        >>> eq_(table.sleep_time(60), 60)
        >>> eq_(table.sleep_time(62), 58)
        >>> eq_(table.sleep_time(3590, time_speedup=1), 10)
        >>> eq_(table.sleep_time(12543, time_speedup=1), 1857)
        >>> eq_(table.sleep_time(12543, time_speedup=1, sleep_factor=2), 57)
        >>> eq_(table.sleep_time(12600, time_speedup=1, sleep_factor=2), 1800)
        >>> eq_(table.sleep_time(1, time_speedup=60, sleep_factor=1), 59)
        >>> eq_(table.sleep_time(1, time_speedup=60, sleep_factor=2), 29)
        >>> eq_(table.sleep_time(30, time_speedup=60, sleep_factor=2), 30)
        >>> table.time_range = 1
        >>> eq_(table.sleep_time(1, time_speedup=1), 149)
        """
        # 150 = 3600 / 24
        d = self.time_range * 150 / ((time_speedup or self.time_speedup) * (sleep_factor or self.sleep_factor))
        return math.ceil(d - (total_seconds(time) % d))
