"""
Module related to enumeration.
"""
from __future__ import annotations

from typing import Any
import enum

__all__ = ['OrderedEnum']


class OrderedEnum(enum.Enum):
    """
    An enumeration both hash-able and ordered by value.

    Reference: https://docs.python.org/3/library/enum.html#orderedenum.
    """

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value == other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value >= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value > other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value <= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value != other.value  # pylint:disable=comparison-with-callable
        return NotImplemented
