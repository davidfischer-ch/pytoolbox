"""
Extra fields for your models.
"""
from __future__ import annotations

import math
import os

from django.conf import settings
from django.db import models
from django.core import validators as dj_validators
from django.db.models.fields import files
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from pytoolbox import module
from pytoolbox.django.core import validators
from . import mixins

_all = module.All(globals())


# Char & Text

class CharField(mixins.OptionsMixin, mixins.NullifyMixin, models.CharField):
    """A CharFiled with OptionsMixin and NullifyMixin applied."""


class TextField(mixins.OptionsMixin, mixins.NullifyMixin, models.TextField):
    """A TextField with OptionsMixin and NullifyMixin applied."""


class StripCharField(mixins.OptionsMixin, mixins.StripMixin, mixins.NullifyMixin, models.CharField):
    """A CharFiled with OptionsMixin, StripMixin and NullifyMixin applied."""


class StripTextField(mixins.OptionsMixin, mixins.StripMixin, mixins.NullifyMixin, models.TextField):
    """A TextField with OptionsMixin, StripMixin and NullifyMixin applied."""


class ExtraChoicesField(StripCharField):
    """Allow additional choices beyond those defined in the field's ``choices``."""

    def __init__(
            self,
            verbose_name: str | None = None,
            extra_choices: list | None = None,
            **kwargs: object) -> None:
        self.extra_choices = extra_choices or []
        super().__init__(verbose_name=verbose_name, **kwargs)

    def deconstruct(self) -> tuple[str, str, list, dict]:
        """Include ``extra_choices`` in the field's deconstructed representation."""
        name, path, args, kwargs = super().deconstruct()
        if self.extra_choices:
            kwargs['extra_choices'] = self.extra_choices
        return name, path, args, kwargs

    def validate(self, value: object, model_instance: object) -> None:
        """Validate against both standard and extra choices."""
        choices = self._choices
        try:
            self._choices = list(self.choices) + list(self.extra_choices)
            return super().validate(value, model_instance)
        finally:
            self._choices = choices


# Date and time

class CreatedAtField(mixins.OptionsMixin, models.DateTimeField):
    """Auto-set datetime field for creation timestamps."""

    default_options = {'default': now, 'editable': False, 'verbose_name': _('Created at')}


class UpdatedAtField(mixins.OptionsMixin, models.DateTimeField):
    """Auto-updated datetime field for modification timestamps."""

    default_options = {'auto_now': True, 'editable': False, 'verbose_name': _('Updated at')}


# Miscellaneous

class CreatedByField(mixins.OptionsMixin, models.ForeignKey):
    """Non-editable foreign key to the user who created the instance."""

    default_options = {'to': settings.AUTH_USER_MODEL, 'editable': False}


class MD5ChecksumField(StripCharField):
    """Char field validated as a 32-character hexadecimal MD5 checksum."""

    default_error_messages = {'invalid': _('Enter a valid MD5 checksum')}
    default_options = {'max_length': 32}
    default_validators = [validators.MD5ChecksumValidator()]


class MoneyField(mixins.OptionsMixin, models.DecimalField):
    """Decimal field pre-configured with min/max validators for monetary values."""

    def __init__(self, max_value: int, decimal_places: int = 2, **kwargs: object) -> None:
        self.max_value = max_value
        super().__init__(
            decimal_places=decimal_places,
            max_digits=int(math.log10(max_value)) + 3,
            validators=[
                dj_validators.MinValueValidator(0),
                dj_validators.MaxValueValidator(max_value)
            ],
            **kwargs)

    def deconstruct(self) -> tuple[str, str, list, dict]:
        """Reconstruct with ``max_value`` as the sole positional argument."""
        name, path, args, kwargs = super(MoneyField, self).deconstruct()
        kwargs.pop('decimal_places', None)
        kwargs.pop('max_digits', None)
        kwargs.pop('validators', None)
        return name, path, [self.max_value], kwargs


class URLField(StripCharField, models.URLField):
    """An URLFIeld with StripCharField behavior inside."""

    default_options = {'max_length': 8000}  # http://tools.ietf.org/html/rfc7230#section-3.1.1


# Storage

class FieldFile(files.FieldFile):
    """Extended :class:`~django.db.models.fields.files.FieldFile` with basename helpers."""

    @property
    def basename(self) -> str | None:
        """Return the base name of the file or ``None`` if empty."""
        return os.path.basename(self.name) if self else None

    @basename.setter
    def basename(self, value: str) -> None:
        # TODO use storage.get_valid_name
        self.name = self.field.upload_to(self.instance, os.path.basename(value))
        setattr(self.instance, self.field.name, self.name)

    @property
    def exists(self) -> bool:
        """Return ``True`` if the file exists in storage."""
        return bool(self) and self.storage.exists(self.name)


class FileField(mixins.OptionsMixin, models.FileField):
    """A FileField with OptionsMixin applied."""

    attr_class = FieldFile


__all__ = _all.diff(globals())
