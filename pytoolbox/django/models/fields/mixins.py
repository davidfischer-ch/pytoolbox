"""
Mix-ins for building your own models fields.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pytoolbox.compat import override
from pytoolbox.django.core import validators

if TYPE_CHECKING:
    from django.db import models

# Each mixin below completes a model field and reads its attributes (`attname`, `null`, `pre_save`,
# ...); naming the base under TYPE_CHECKING states that for the checker only.
_FieldMixin = models.Field if TYPE_CHECKING else object

__all__ = ['LowerCaseMixin', 'OptionsMixin', 'StripMixin']


class LowerCaseMixin(_FieldMixin):
    """Convert field values to lowercase before saving to the database."""

    @override
    def get_prep_value(self, value: str | None) -> str | None:
        """Return the value lowercased for database storage."""
        value = super().get_prep_value(value)
        if value is not None:
            value = value.lower()
        return value


class NullifyMixin(_FieldMixin):
    """Replace falsy values by None if NULL is allowed."""

    @override
    def pre_save(self, model_instance: models.Model, add: bool) -> object:
        """Set the field to ``None`` if the value is falsy and NULL is allowed."""
        value = super().pre_save(model_instance, add)
        if not value and self.null:
            value = None
            setattr(model_instance, self.attname, value)
        return value


class OptionsMixin(_FieldMixin):
    """Apply default and override keyword arguments to field constructors."""

    default_options: ClassVar[dict[str, Any]] = {}
    override_options: ClassVar[dict[str, Any]] = {}

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**{**self.default_options, **kwargs, **self.override_options})


class StripMixin(_FieldMixin):
    """Strip whitespace (see Django ticket 6362)."""

    default_validators = [validators.EmptyValidator()]  # noqa: RUF012

    @override
    def pre_save(self, model_instance: models.Model, add: bool) -> str | None:
        """Strip leading and trailing whitespace before saving."""
        value = super().pre_save(model_instance, add)
        if value:
            value = value.strip()
            setattr(model_instance, self.attname, value)
        return value
