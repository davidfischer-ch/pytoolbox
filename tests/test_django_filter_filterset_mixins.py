from __future__ import annotations

import pytest

from pytoolbox.django_filter.filterset import mixins


def test_raise_on_unhandled_field_class_with_value() -> None:
    """Passes through the filter when the parent returns a non-None value."""

    class Base:
        """Base class providing filter_for_field method."""

        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            """Return a filter for the given field."""
            return 'some_filter'

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        """FilterSet combining the mixin with the base implementation."""

        pass

    assert FakeFilterSet.filter_for_field('field', 'name') == 'some_filter'


def test_raise_on_unhandled_field_class_without_value() -> None:
    """Raises NotImplementedError when the parent returns None (no suitable filter)."""

    class Base:
        """Base class returning None from filter_for_field."""

        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            """Return None to simulate no suitable filter."""
            return None

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        """FilterSet that will raise an error due to unhandled field."""

        pass

    with pytest.raises(NotImplementedError, match='Unable to find a suitable filter'):
        FakeFilterSet.filter_for_field('field', 'name')


def test_raise_on_unhandled_field_class_with_lookup_type() -> None:
    """Error message includes the lookup_type when a non-default lookup is used."""

    class Base:
        """Base class for testing lookup_type in error message."""

        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            """Return None to trigger NotImplementedError."""
            return None

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        """FilterSet for testing lookup_type inclusion in error."""

        pass

    with pytest.raises(NotImplementedError, match='icontains'):
        FakeFilterSet.filter_for_field('field', 'name', lookup_type='icontains')
