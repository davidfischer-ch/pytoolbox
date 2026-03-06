"""
Mix-ins for building your own models fields.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox.django.core import validators

if TYPE_CHECKING:
    from django.db import models

__all__ = ['LowerCaseMixin', 'OptionsMixin', 'StripMixin']


class LowerCaseMixin(object):
    """Convert field values to lowercase before saving to the database."""

    def get_prep_value(self, value: str | None) -> str | None:
        """Return the value lowercased for database storage."""
        value = super().get_prep_value(value)
        if value is not None:
            value = value.lower()
        return value


class NullifyMixin(object):
    """Replace falsy values by None if NULL is allowed."""

    def pre_save(self, model_instance: models.Model, add: bool) -> object:
        """Set the field to ``None`` if the value is falsy and NULL is allowed."""
        value = super().pre_save(model_instance, add)
        if not value and self.null:
            value = None
            setattr(model_instance, self.attname, value)
        return value


class OptionsMixin(object):
    """Apply default and override keyword arguments to field constructors."""

    default_options = {}
    override_options = {}

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**{**self.default_options, **kwargs, **self.override_options})


class StripMixin(object):
    """https://code.djangoproject.com/ticket/6362#no1"""

    default_validators = [validators.EmptyValidator()]

    def pre_save(self, model_instance: models.Model, add: bool) -> str | None:
        """Strip leading and trailing whitespace before saving."""
        value = super().pre_save(model_instance, add)
        if value:
            value = value.strip()
            setattr(model_instance, self.attname, value)
        return value
