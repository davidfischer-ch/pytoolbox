# -*- encoding: utf-8 -*-

"""
Module related to enumeration.

.. note::

    The :class:`pytoolbox.enum.OrderedEnum` is made available when the :mod:`enum` is available.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    import enum
except ImportError:
    pass
else:
    import functools

    @functools.total_ordering
    class OrderedEnum(enum.Enum):
        """An enumeration both hash-able and ordered by value."""

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            if self.__class__ is other.__class__:
                return self.value == other.value
            return NotImplemented

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented
