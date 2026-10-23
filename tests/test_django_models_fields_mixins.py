"""Tests for the django.models.fields.mixins module."""

from __future__ import annotations

from typing import Any, ClassVar

from django.db import models

from pytoolbox.django.models.fields import mixins


class NullableNoteField(mixins.OptionsMixin, models.TextField):
    """A field whose defaults differ from Django's own: nullable, blank, and labelled."""

    default_options: ClassVar[dict[str, Any]] = {
        'blank': True,
        'null': True,
        'verbose_name': 'Note',
    }


# --- OptionsMixin ---------------------------------------------------------------------------------


def test_options_mixin_applies_the_defaults_a_site_leaves_out() -> None:
    """A bare declaration takes every default option."""
    field = NullableNoteField()

    assert (field.null, field.blank, field.verbose_name) == (True, True, 'Note')


def test_options_mixin_clone_keeps_an_option_set_back_to_django_default() -> None:
    """`null=False` survives the clone a migration rebuilds the field from."""
    field = NullableNoteField(null=False, blank=False)

    _, _, _, kwargs = field.deconstruct()
    clone = field.clone()

    assert (kwargs['null'], kwargs['blank']) == (False, False)
    assert (clone.null, clone.blank) == (False, False)


def test_options_mixin_deconstruct_adds_nothing_for_the_defaults_kept() -> None:
    """A site keeping the class's defaults deconstructs as Django writes it, nothing more."""
    _, _, _, kwargs = NullableNoteField().deconstruct()

    assert kwargs == {'blank': True, 'null': True, 'verbose_name': 'Note'}
