"""Tests for the rest_framework.metadata.mixins module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from rest_framework import serializers
from rest_framework.metadata import SimpleMetadata

from pytoolbox.rest_framework.metadata import mixins

pytestmark = pytest.mark.filterwarnings(
    'ignore:ExcludeRelatedChoicesMixin is deprecated:DeprecationWarning'
)


@pytest.mark.parametrize(
    'field',
    [
        serializers.PrimaryKeyRelatedField(queryset=MagicMock()),
        serializers.PrimaryKeyRelatedField(many=True, queryset=MagicMock()),
    ],
)
def test_exclude_related_choices_omits_the_choices_of_a_related_field(field) -> None:
    """A related field has no choices."""
    assert 'choices' not in _metadata().get_field_info(field)


def test_exclude_related_choices_subclass_is_deprecated() -> None:
    """Subclassing ExcludeRelatedChoicesMixin emits a DeprecationWarning naming its replacement."""
    with pytest.warns(DeprecationWarning, match='SimpleMetadata'):

        class FakeMetadata(mixins.ExcludeRelatedChoicesMixin, SimpleMetadata):  # pylint:disable=unused-variable
            """Fake metadata class combining mixin with base."""


# --- Internals ------------------------------------------------------------------------------------


def _metadata() -> SimpleMetadata:
    """Return a metadata excluding the choices of related fields."""

    class Metadata(mixins.ExcludeRelatedChoicesMixin, SimpleMetadata):
        """Metadata excluding the choices of related fields."""

    return Metadata()
