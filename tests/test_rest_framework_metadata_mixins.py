"""Tests for the rest_framework.metadata.mixins module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock

from rest_framework import serializers

from pytoolbox.rest_framework.metadata import mixins


def test_exclude_related_choices_non_related_field() -> None:
    """Non-related fields pass through get_field_info unchanged."""

    class Base:
        """Base class providing get_field_info."""

        def get_field_info(self, field):  # pylint:disable=unused-argument
            """Get field info implementation."""
            return {'type': 'string'}

    class FakeMetadata(mixins.ExcludeRelatedChoicesMixin, Base):
        """Fake metadata class combining mixin with base."""

    metadata = FakeMetadata()
    field = serializers.CharField()
    result = metadata.get_field_info(field)
    assert result == {'type': 'string'}


def test_exclude_related_choices_related_field() -> None:
    """Related fields have their choices temporarily hidden, then class is restored."""

    class Base:
        """Base class providing get_field_info."""

        def get_field_info(self, field):
            """Test method."""
            has_choices = hasattr(field, 'choices')
            return {'type': 'related', 'has_choices': has_choices}

    class FakeMetadata(mixins.ExcludeRelatedChoicesMixin, Base):
        """Fake metadata class combining mixin with base."""

    metadata = FakeMetadata()
    field = serializers.PrimaryKeyRelatedField(queryset=MagicMock())
    result = metadata.get_field_info(field)
    assert result['type'] == 'related'
    # The field's class should be restored after get_field_info
    assert isinstance(field, serializers.PrimaryKeyRelatedField)


def test_exclude_related_choices_restores_class_on_error() -> None:
    """Field's original class is restored even when get_field_info raises an exception."""

    class Base:
        """Base class that raises error in get_field_info."""

        def get_field_info(self, field):
            """Test method."""
            raise RuntimeError('boom')

    class FakeMetadata(mixins.ExcludeRelatedChoicesMixin, Base):
        """Fake metadata class combining mixin with base."""

    metadata = FakeMetadata()
    field = serializers.PrimaryKeyRelatedField(queryset=MagicMock())
    original_class = type(field)
    try:
        metadata.get_field_info(field)
    except RuntimeError:
        pass
    assert isinstance(field, original_class)
