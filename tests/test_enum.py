"""Tests for the enum module."""

# pylint:disable=unnecessary-dunder-call
from __future__ import annotations

from pytoolbox import enum


class Priority(enum.OrderedEnum):
    """Priority enum for testing OrderedEnum functionality."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def test_hash() -> None:
    """Members are hashable based on their value."""
    assert hash(Priority.LOW) == hash(1)
    assert hash(Priority.HIGH) == hash(3)
    # Usable as dict keys
    d = {Priority.LOW: 'low', Priority.HIGH: 'high'}
    assert d[Priority.LOW] == 'low'


def test_eq() -> None:
    """Equal members compare as equal."""
    assert Priority.LOW == Priority.LOW
    assert Priority.LOW != Priority.HIGH


def test_ne() -> None:
    """Unequal members compare as not equal."""
    assert Priority.LOW != Priority.HIGH
    assert Priority.LOW == Priority.LOW


def test_lt() -> None:
    """Less-than compares by value."""
    assert Priority.LOW < Priority.MEDIUM
    assert Priority.MEDIUM >= Priority.LOW


def test_le() -> None:
    """Less-than-or-equal compares by value."""
    assert Priority.LOW <= Priority.LOW
    assert Priority.LOW <= Priority.MEDIUM
    assert Priority.HIGH > Priority.LOW


def test_gt() -> None:
    """Greater-than compares by value."""
    assert Priority.HIGH > Priority.MEDIUM
    assert Priority.LOW <= Priority.MEDIUM


def test_ge() -> None:
    """Greater-than-or-equal compares by value."""
    assert Priority.HIGH >= Priority.HIGH
    assert Priority.HIGH >= Priority.MEDIUM
    assert Priority.LOW < Priority.MEDIUM


def test_sorting() -> None:
    """Members can be sorted by value."""
    items = [Priority.HIGH, Priority.LOW, Priority.MEDIUM]
    assert sorted(items) == [
        Priority.LOW,
        Priority.MEDIUM,
        Priority.HIGH,
    ]


def test_eq_different_type_returns_not_implemented() -> None:
    """Comparing with a non-member returns NotImplemented."""
    assert Priority.LOW.__eq__(42) is NotImplemented


def test_ne_different_type_returns_not_implemented() -> None:
    """Ne with a non-member returns NotImplemented."""
    assert Priority.LOW.__ne__(42) is NotImplemented


def test_lt_different_type_returns_not_implemented() -> None:
    """Lt with a non-member returns NotImplemented."""
    assert Priority.LOW.__lt__(42) is NotImplemented


def test_le_different_type_returns_not_implemented() -> None:
    """Le with a non-member returns NotImplemented."""
    assert Priority.LOW.__le__(42) is NotImplemented


def test_gt_different_type_returns_not_implemented() -> None:
    """Gt with a non-member returns NotImplemented."""
    assert Priority.LOW.__gt__(42) is NotImplemented


def test_ge_different_type_returns_not_implemented() -> None:
    """Ge with a non-member returns NotImplemented."""
    assert Priority.LOW.__ge__(42) is NotImplemented


def test_usable_in_set() -> None:
    """Members can be placed in a set (hashable + eq)."""
    s = {Priority.LOW, Priority.LOW, Priority.HIGH}
    assert len(s) == 2


def test_cross_enum_comparison() -> None:
    """
    Comparing members of different OrderedEnum subclasses
    returns NotImplemented.
    """

    class Other(enum.OrderedEnum):
        """Another enum for cross-enum comparison test."""

        A = 1

    assert Priority.LOW.__eq__(Other.A) is NotImplemented
    assert Priority.LOW.__lt__(Other.A) is NotImplemented
