"""Tests for the django.forms.fields module."""

from __future__ import annotations

from pytoolbox.django.forms import fields


def test_strip_char_field_rejects_whitespace() -> None:
    """StripCharField uses a regex that rejects whitespace-only input."""
    field = fields.StripCharField()
    assert field.regex.pattern == '\\S+'


def test_strip_char_field_default_widget_attrs() -> None:
    """Default widget has autofocus attribute."""
    field = fields.StripCharField()
    assert field.widget.attrs.get('autofocus') == 'autofocus'


def test_strip_char_field_custom_widget_attrs() -> None:
    """Custom widget_attrs are merged with defaults."""
    field = fields.StripCharField(
        widget_attrs={'placeholder': 'Search...'},
    )
    assert field.widget.attrs.get('autofocus') == 'autofocus'
    assert field.widget.attrs.get('placeholder') == 'Search...'


def test_strip_char_field_max_length() -> None:
    """max_length defaults to None."""
    field = fields.StripCharField()
    assert field.max_length is None


def test_strip_char_field_none_widget_attrs() -> None:
    """Passing widget_attrs=None uses only defaults."""
    field = fields.StripCharField(widget_attrs=None)
    assert field.widget.attrs.get('autofocus') == 'autofocus'
