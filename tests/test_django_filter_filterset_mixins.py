"""Tests for the django_filter.filterset.mixins module."""
# pylint:disable=too-few-public-methods

from __future__ import annotations

import pytest
from django.db import models
from django_filters import FilterSet

from pytoolbox.django_filter.filterset import mixins

pytestmark = pytest.mark.filterwarnings(
    'ignore:RaiseOnUnhandledFieldClassMixin is deprecated:DeprecationWarning'
)


class Document(models.Model):
    """Model with a field django-filter has no filter for."""

    data = models.JSONField()

    class Meta:
        """Meta options."""

        app_label = 'test'


def test_raise_on_unhandled_field_class_rejects_an_unhandled_field() -> None:
    """A filter set on a field with no matching filter class fails at its creation."""
    with pytest.raises(AssertionError, match='unrecognized field type JSONField'):

        class DocumentFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, FilterSet):  # pylint:disable=unused-variable
            """Filter set on the unhandled field."""

            class Meta:
                """Meta options."""

                fields = ['data']
                model = Document


def test_raise_on_unhandled_field_class_subclass_is_deprecated() -> None:
    """Subclassing RaiseOnUnhandledFieldClassMixin emits a DeprecationWarning naming the option."""
    with pytest.warns(DeprecationWarning, match='unknown_field_behavior'):

        class DocumentFilterSet(mixins.RaiseOnUnhandledFieldClassMixin, FilterSet):  # pylint:disable=unused-variable
            """Filter set with the mixin."""
