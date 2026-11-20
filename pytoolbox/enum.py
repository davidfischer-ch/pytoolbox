"""
Module related to enumeration.
"""

from __future__ import annotations

import enum
from typing import Any

__all__ = ['OrderedEnum', 'find_member']


class OrderedEnum(enum.Enum):
    """
    An enumeration both hash-able and ordered by value.

    Reference: https://docs.python.org/3/library/enum.html#orderedenum.
    """

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value == other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value >= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value > other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value <= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value < other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if type(self) is type(other):
            return self.value != other.value  # pylint:disable=comparison-with-callable
        return NotImplemented


def find_member[EnumT: enum.Enum](enum_class: type[EnumT], value: Any) -> EnumT | None:
    """
    Return the member of `enum_class` holding `value`, or ``None`` if none does.

    A member passed as `value` is returned as is.

    **Example usage**

    >>> class Color(enum.Enum):
    ...     RED = 1
    ...     GREEN = 2
    ...
    >>> find_member(Color, 2)
    <Color.GREEN: 2>
    >>> find_member(Color, Color.RED)
    <Color.RED: 1>
    >>> find_member(Color, 3) is None
    True
    >>> find_member(Color, None) is None
    True
    """
    try:
        return enum_class(value)
    except ValueError:
        return None
