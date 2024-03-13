"""
Mix-ins for building your own models fields.
"""
from __future__ import annotations

from pytoolbox.django.core import validators

__all__ = ['LowerCaseMixin', 'OptionsMixin', 'StripMixin']


class LowerCaseMixin(object):

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is not None:
            value = value.lower()
        return value


class NullifyMixin(object):
    """Replace falsy values by None if NULL is allowed."""

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if not value and self.null:
            value = None
            setattr(model_instance, self.attname, value)
        return value


class OptionsMixin(object):

    default_options = {}
    override_options = {}

    def __init__(self, **kwargs):
        super().__init__(**{**self.default_options, **kwargs, **self.override_options})


class StripMixin(object):
    """https://code.djangoproject.com/ticket/6362#no1"""

    default_validators = [validators.EmptyValidator()]

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if value:
            value = value.strip()
            setattr(model_instance, self.attname, value)
        return value
