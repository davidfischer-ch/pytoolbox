"""
Module related to enumeration.
"""

import enum


class OrderedEnum(enum.Enum):
    """
    An enumeration both hash-able and ordered by value.

    Reference: https://docs.python.org/3/library/enum.html#orderedenum.
    """

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value  # pylint:disable=comparison-with-callable
        return NotImplemented

    def __ne__(self, other):
        if self.__class__ is other.__class__:
            return self.value != other.value  # pylint:disable=comparison-with-callable
        return NotImplemented
