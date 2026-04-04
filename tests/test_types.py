"""Tests for the types module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

import copy

from pytoolbox import types


def test_missing() -> None:
    """Missing sentinel is falsy, displays as 'Missing', and is preserved through copy/deepcopy."""
    assert f'{types.Missing}' == 'Missing'
    assert types.Missing is not False
    assert bool(types.Missing) is False
    assert copy.copy(types.Missing) is types.Missing
    assert copy.deepcopy(types.Missing) is types.Missing


def test_get_properties() -> None:
    """Only properties are yielded, not regular methods."""

    class MyObj:
        """Test class with properties and a method."""

        @property
        def name(self):
            """Return name property."""
            return 'hello'

        @property
        def value(self):
            """Return value property."""
            return 42

        def method(self):
            """Regular method (not a property)."""

    obj = MyObj()
    props = dict(types.get_properties(obj))
    assert props == {'name': 'hello', 'value': 42}


def test_merge_bases_attribute() -> None:
    """Attribute values are accumulated through the MRO using merge_func."""

    class Base:
        """Base class with items."""

        items = [1, 2]

    class Child(Base):
        """Child class with additional items."""

        items = [3]

    class GrandChild(Child):
        """GrandChild class with additional items."""

        items = [4]

    result = types.merge_bases_attribute(GrandChild, 'items', [], [])
    # MRO: GrandChild -> Child -> Base -> object
    # [] + [4] (GrandChild) + [3] (Child) + [1, 2] (Base) + [] (object)
    assert result == [4, 3, 1, 2]


def test_merge_bases_attribute_with_default() -> None:
    """Classes missing the attribute use the default value."""

    class A:
        """Class without tags attribute."""

    class B(A):
        """Class with tags attribute."""

        tags = ('x',)

    result = types.merge_bases_attribute(B, 'tags', (), ())
    # MRO: B -> A -> object; A and object have no 'tags' so default () is used
    assert result == ('x',)
