"""Pytoolbox's Template tag and filters."""

from __future__ import annotations

from django import template
from django.conf import settings
from django.template.backends.django import DjangoTemplates
from django.utils.module_loading import import_string

from pytoolbox import module

_all = module.All(globals())

# The option of the first DjangoTemplates engine, else Django's default.
string_if_invalid: str = next(
    (
        engine.get('OPTIONS', {}).get('string_if_invalid', '')
        for engine in settings.TEMPLATES
        if issubclass(import_string(engine['BACKEND']), DjangoTemplates)
    ),
    '',
)

register = template.Library()

# Submodule imports come after register/string_if_invalid since they import both from here, and
# they are re-exports: __all__ is computed at the end of the module, which ruff cannot see.
# ruff: noqa: E402, F401
from .exif import (
    EXPOSURE_MODE_LABELS,
    ORIENTATION_LABELS,
    SENSING_METHOD_LABELS,
    WHITE_BALANCE_LABELS,
    exposure_mode,
    orientation,
    sensing_method,
    white_balance,
)
from .humanize import duration, naturalbitrate, naturalfilesize
from .miscellaneous import (
    LABEL_TO_CLASS,
    NUMERIC_TEST,
    StaticPathNode,
    getattribute,
    inline,
    rst_title,
    secs_to_time,
    static_abspath,
    status_label,
    timedelta,
    verbose_name,
    verbose_name_plural,
)

__all__ = _all.diff(globals())
