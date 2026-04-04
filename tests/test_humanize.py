"""Tests for the humanize module."""

from __future__ import annotations

from pytoolbox import humanize


def test_pluralize_singular() -> None:
    """Returns singular form when number is exactly 1."""
    assert humanize.pluralize(1, 'item', 'items') == 'item'


def test_pluralize_singular_negative() -> None:
    """Returns singular form when number is -1."""
    assert humanize.pluralize(-1, 'item', 'items') == 'item'


def test_pluralize_plural_zero() -> None:
    """Returns plural form when number is 0."""
    assert humanize.pluralize(0, 'item', 'items') == 'items'


def test_pluralize_plural_many() -> None:
    """Returns plural form when number is greater than 1."""
    assert humanize.pluralize(2, 'item', 'items') == 'items'
    assert humanize.pluralize(100, 'item', 'items') == 'items'
