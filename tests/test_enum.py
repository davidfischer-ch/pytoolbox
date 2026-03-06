# pylint:disable=unnecessary-dunder-call
from __future__ import annotations

from pytoolbox import enum


class Priority(enum.OrderedEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TestOrderedEnum:
    """Tests for OrderedEnum comparison and hashing."""

    def test_hash(self) -> None:
        """Members are hashable based on their value."""
        assert hash(Priority.LOW) == hash(1)
        assert hash(Priority.HIGH) == hash(3)
        # Usable as dict keys
        d = {Priority.LOW: 'low', Priority.HIGH: 'high'}
        assert d[Priority.LOW] == 'low'

    def test_eq(self) -> None:
        """Equal members compare as equal."""
        assert Priority.LOW == Priority.LOW
        assert Priority.LOW != Priority.HIGH

    def test_ne(self) -> None:
        """Unequal members compare as not equal."""
        assert Priority.LOW != Priority.HIGH
        assert Priority.LOW == Priority.LOW

    def test_lt(self) -> None:
        """Less-than compares by value."""
        assert Priority.LOW < Priority.MEDIUM
        assert Priority.MEDIUM >= Priority.LOW

    def test_le(self) -> None:
        """Less-than-or-equal compares by value."""
        assert Priority.LOW <= Priority.LOW
        assert Priority.LOW <= Priority.MEDIUM
        assert Priority.HIGH > Priority.LOW

    def test_gt(self) -> None:
        """Greater-than compares by value."""
        assert Priority.HIGH > Priority.MEDIUM
        assert Priority.LOW <= Priority.MEDIUM

    def test_ge(self) -> None:
        """Greater-than-or-equal compares by value."""
        assert Priority.HIGH >= Priority.HIGH
        assert Priority.HIGH >= Priority.MEDIUM
        assert Priority.LOW < Priority.MEDIUM

    def test_sorting(self) -> None:
        """Members can be sorted by value."""
        items = [Priority.HIGH, Priority.LOW, Priority.MEDIUM]
        assert sorted(items) == [
            Priority.LOW,
            Priority.MEDIUM,
            Priority.HIGH
        ]

    def test_eq_different_type_returns_not_implemented(self) -> None:
        """Comparing with a non-member returns NotImplemented."""
        assert Priority.LOW.__eq__(42) is NotImplemented

    def test_ne_different_type_returns_not_implemented(self) -> None:
        """ne with a non-member returns NotImplemented."""
        assert Priority.LOW.__ne__(42) is NotImplemented

    def test_lt_different_type_returns_not_implemented(self) -> None:
        """lt with a non-member returns NotImplemented."""
        assert Priority.LOW.__lt__(42) is NotImplemented

    def test_le_different_type_returns_not_implemented(self) -> None:
        """le with a non-member returns NotImplemented."""
        assert Priority.LOW.__le__(42) is NotImplemented

    def test_gt_different_type_returns_not_implemented(self) -> None:
        """gt with a non-member returns NotImplemented."""
        assert Priority.LOW.__gt__(42) is NotImplemented

    def test_ge_different_type_returns_not_implemented(self) -> None:
        """ge with a non-member returns NotImplemented."""
        assert Priority.LOW.__ge__(42) is NotImplemented

    def test_usable_in_set(self) -> None:
        """Members can be placed in a set (hashable + eq)."""
        s = {Priority.LOW, Priority.LOW, Priority.HIGH}
        assert len(s) == 2

    def test_cross_enum_comparison(self) -> None:
        """Comparing members of different OrderedEnum subclasses
        returns NotImplemented."""
        class Other(enum.OrderedEnum):
            A = 1

        assert Priority.LOW.__eq__(Other.A) is NotImplemented
        assert Priority.LOW.__lt__(Other.A) is NotImplemented
