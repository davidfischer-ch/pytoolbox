"""Pytoolbox's Template tag and filters."""
from __future__ import annotations

from django import template
from django.conf import settings

from pytoolbox import module

_all = module.All(globals())

string_if_invalid = ''  # Official default value
try:  # Django >= 1.8
    string_if_invalid = settings.TEMPLATES['OPTIONS']['string_if_invalid']
except (KeyError, TypeError):
    try:  # Django < 1.8
        string_if_invalid = settings.TEMPLATE_STRING_IF_INVALID
    except AttributeError:
        pass  # Use default

register = template.Library()

# Submodule imports come after register/string_if_invalid since they import both from here.
from .exif import (
    EXPOSURE_MODE_LABELS,
    ORIENTATION_LABELS,
    SENSING_METHOD_LABELS,
    WHITE_BALANCE_LABELS,
    exposure_mode,
    orientation,
    sensing_method,
    white_balance
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
    verbose_name_plural
)

__all__ = _all.diff(globals())
