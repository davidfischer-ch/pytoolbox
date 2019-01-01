# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, math

from . import module
from .datetime import total_seconds
from .encoding import string_types

_all = module.All(globals())


class EventsTable(object):
    """Scan a spare events table and replace missing entry by previous (non empty) entry."""

    def __init__(self, sparse_events_table, time_range, time_speedup, sleep_factor=1.0):
        self.time_range, self.time_speedup, self.sleep_factor = \
            time_range, time_speedup, sleep_factor
        previous_event = sparse_events_table[0]
        self.events = {}
        for index in xrange(self.time_range):  # noqa
            event = sparse_events_table.get(index, previous_event)
            self.events[index] = event
            previous_event = event

    def get(self, time, time_speedup=None, default_value=None):
        # """
        # >>> from pytoolbox.unittest import asserts
        # >>> def test_get_index(time_range, time_speedup):
        # ...     table = EventsTable({0: 'salut'}, time_range, time_speedup)
        # ...     modulo = previous = 0
        # ...     for t in xrange(24*3600+1):
        # ...         index = table.get(t+2*60, time_range, time_speedup)[0]
        # ...         if previous > index:
        # ...             modulo += 1
        # ...         assert(0 <= index < time_range)
        # ...         previous = index
        # ...     asserts.equal(modulo, time_speedup)

        # Test get_index with a speedup of 1440 (maps 1 minute to 24 hours):
        # >>> test_get_index(24, 24 * 60)

        # Test get_index with a speedup of 12 (maps 2 hours to 24 hours):
        # >>> test_get_index(24, 12)
        # """
        index = int(
            (total_seconds(time) * ((time_speedup or self.time_speedup) / 3600) % self.time_range))
        return index, self.events.get(index, default_value)

    def sleep_time(self, time, time_speedup=None, sleep_factor=None):
        """
        Return required sleep time to wait for next scheduled event.

        **Example usage**

        >>> from pytoolbox.unittest import asserts
        >>> table = EventsTable({0: 'salut'}, 24, 60)
        >>> asserts.equal(table.sleep_time(1), 59)
        >>> asserts.equal(table.sleep_time(58), 2)
        >>> asserts.equal(table.sleep_time(60), 60)
        >>> asserts.equal(table.sleep_time(62), 58)
        >>> asserts.equal(table.sleep_time(3590, time_speedup=1), 10)
        >>> asserts.equal(table.sleep_time(12543, time_speedup=1), 1857)
        >>> asserts.equal(table.sleep_time(12543, time_speedup=1, sleep_factor=2), 57)
        >>> asserts.equal(table.sleep_time(12600, time_speedup=1, sleep_factor=2), 1800)
        >>> asserts.equal(table.sleep_time(1, time_speedup=60, sleep_factor=1), 59)
        >>> asserts.equal(table.sleep_time(1, time_speedup=60, sleep_factor=2), 29)
        >>> asserts.equal(table.sleep_time(30, time_speedup=60, sleep_factor=2), 30)
        >>> table.time_range = 1
        >>> asserts.equal(table.sleep_time(1, time_speedup=1), 149)
        """
        # 150 = 3600 / 24
        d = self.time_range * 150 / (
            (time_speedup or self.time_speedup) * (sleep_factor or self.sleep_factor))
        return math.ceil(d - (total_seconds(time) % d))


class pygal_deque(collections.deque):
    """
    A deque None'ing duplicated values to produce nicer `pygal <pygal.org>`_ line charts
    (e.g. 5555322211111 -> 5__532_21___1).

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
            for index in xrange(len(self_list)):  # noqa
                if self_list[index] is None:
                    self_list[index] = previous
                else:
                    previous = self_list[index]
        return self_list


def flatten_dict(the_dict, key_template='{0}.{1}'):
    """
    Flatten the keys of a nested dictionary. Nested keys will be appended iteratively using given
    `key_template`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.dict_equal(flatten_dict({'a': 'b', 'c': 'd'}), {'a': 'b', 'c': 'd'})
    >>> asserts.dict_equal(flatten_dict({'a': {'b': {'c': ['d', 'e']}, 'f': 'g'}}), {'a.b.c': ['d', 'e'], 'a.f': 'g'})
    >>> asserts.dict_equal(flatten_dict({'a': {'b': {'c': ['d', 'e']}, 'f': 'g'}}, '{1}-{0}'),
    ...                    {'c-b-a': ['d', 'e'], 'f-a': 'g'})
    """
    def expand_item(key, value):
        if isinstance(value, dict):
            return [(key_template.format(key, k), v) for k, v in flatten_dict(value, key_template).iteritems()]
        else:
            return [(key, value)]
    return dict(item for k, v in the_dict.iteritems() for item in expand_item(k, v))


def merge_dicts(*dicts):
    """
    Return a dictionary from multiple dictionaries.

    .. warning::

        This operation is not commutative.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.dict_equal(merge_dicts({'a': 1, 'b': 2}, {'b': 3, 'c': 4}, {'c': 5}), {'a': 1, 'b': 3, 'c': 5})
    >>> asserts.dict_equal(merge_dicts({'c': 5}, {'b': 3, 'c': 4}, {'a': 1, 'b': 2}), {'a': 1, 'b': 2, 'c': 4})
    """
    merged_dict = {}
    set(merged_dict.update(d) for d in dicts)
    return merged_dict


def swap_dict_of_values(the_dict, type=set, method=set.add):  # pylint:disable=redefined-builtin
    """
    Return a dictionary (:class:`collections.defaultdict`) with keys and values swapped.

    This algorithm expect that the values are a container with objects, not a single object.
    Set type to None if values are unique and you want keys to be the values.

    **Example usage**

    Simple swap:

    >>> result = swap_dict_of_values({'odd': [1, 3], 'even': (0, 2)}, type=None)
    >>> assert result == {0: 'even', 1: 'odd', 2: 'even', 3: 'odd'}

    Complex swap:

    >>> result = swap_dict_of_values({'odd': [1, 3], 'even': (0, 2), 'fib': {1, 2, 3}}, type=list, method=list.append)
    >>> assert ({k: sorted(v) for k, v in result.iteritems()} ==
    ...         {0: ['even'], 1: ['fib', 'odd'], 2: ['even', 'fib'], 3: ['fib', 'odd']})
    >>> assert swap_dict_of_values({'odd': [1, 3], 'even': (0, 2), 'f': {1, 2, 3}}, method='add')[2] == {'even', 'f'}
    >>> assert swap_dict_of_values({'bad': 'ab', 'example': 'ab'})['a'] == {'bad', 'example'}
    """
    if type is None:
        reversed_dict = {}
        for key, values in the_dict.iteritems():
            for value in values:
                reversed_dict[value] = key
    else:
        method = getattr(type, method) if isinstance(method, string_types) else method
        reversed_dict = collections.defaultdict(type)
        for key, values in the_dict.iteritems():
            for value in values:
                method(reversed_dict[value], key)
    return reversed_dict


def to_dict_of_values(iterable, type=list, method=list.append):  # pylint:disable=redefined-builtin
    """
    Return a dictionary (:class:`collections.defaultdict`) with key, value pairs merged as
    key -> values.

    **Example usage**

    >>> assert to_dict_of_values([('odd', 1), ('odd', 3), ('even', 0), ('even', 2)]) == {'even': [0, 2], 'odd': [1, 3]}
    >>> assert to_dict_of_values((('a', 1), ('a', 1), ('a', 2)), type=set, method=set.add) == {'a': {1, 2}}
    """
    dict_of_values = collections.defaultdict(type)
    for key, value in iterable:
        method(dict_of_values[key], value)
    return dict_of_values


def window(values, index, delta):
    """
    Extract 1+2*`delta` items from `values` centered at `index` and return a tuple with
    (items, left, right).

    This function tries to simulate a physical slider, meaning the number of extracted elements is
    constant but the centering at `index` is not guaranteed.

    A visual example with 6 `values` and ``delta=1``::

        index = 0  [+++]---  left = 0, right = 2
        index = 1  [+++]---  left = 0, right = 2
        index = 2  -[+++]--  left = 1, right = 3
        index = 3  --[+++]-  left = 2, right = 4
        index = 4  ---[+++]  left = 3, right = 5
        index = 5  ---[+++]  left = 3, right = 5

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> eq = asserts.equal
    >>> eq(window(['a'], 0, 2), (['a'], 0, 0))
    >>> eq(window(['a', 'b', 'c', 'd'], 2, 0), (['c'], 2, 2))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 0, 1), (['a', 'b', 'c'], 0, 2))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 1, 1), (['a', 'b', 'c'], 0, 2))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 2, 1), (['b', 'c', 'd'], 1, 3))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 3, 1), (['c', 'd', 'e'], 2, 4))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 4, 1), (['c', 'd', 'e'], 2, 4))
    >>> eq(window(['a', 'b', 'c', 'd', 'e'], 3, 6), (['a', 'b', 'c', 'd', 'e'], 0, 4))
    >>> eq(window(range(20), 6, 6), ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 0, 12))
    >>> eq(window(range(20), 7, 6), ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 1, 13))
    >>> eq(window(range(20), 10, 6), ([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 4, 16))
    >>> eq(window(range(20), 19, 6), ([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 7, 19))
    """
    length = len(values)
    left, right = index - delta, index + delta
    if left < 0:
        left, right = 0, right - left
    elif right >= length:
        left, right = left - right + length - 1, length - 1
    left, right = max(left, 0), min(right, length - 1)
    return values[left:right + 1], left, right


__all__ = _all.diff(globals())
