from __future__ import annotations

import pytest

from pytoolbox.django_filter.filterset import mixins


def test_raise_on_unhandled_field_class_with_value() -> None:
    class Base:
        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            return 'some_filter'

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        pass

    assert FakeFilterSet.filter_for_field('field', 'name') == 'some_filter'


def test_raise_on_unhandled_field_class_without_value() -> None:
    class Base:
        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            return None

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        pass

    with pytest.raises(NotImplementedError, match='Unable to find a suitable filter'):
        FakeFilterSet.filter_for_field('field', 'name')


def test_raise_on_unhandled_field_class_with_lookup_type() -> None:
    class Base:
        @classmethod
        def filter_for_field(cls, f, name, lookup_type='exact'):  # pylint:disable=unused-argument
            return None

    class FakeFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, Base):
        pass

    with pytest.raises(NotImplementedError, match='icontains'):
        FakeFilterSet.filter_for_field('field', 'name', lookup_type='icontains')
