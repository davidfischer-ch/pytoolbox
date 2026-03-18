"""Miscellaneous template filters and tags."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Final
import collections.abc
import datetime
import os
import re

from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.templatetags.static import PrefixNode, StaticNode
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext as _

from pytoolbox.datetime import secs_to_time as _secs_to_time
from pytoolbox.django.core import constants

from . import register, string_if_invalid

# ==================== ===================== =============== =============== =====================
# description          decorator             arguments       input           output
# ==================== ===================== =============== =============== =====================
# only accept string   @stringfilter         -               is a string [1] return ...
# do not add < > ' " & is_safe=True          -               of any type     return ...
# add HTML < > ' " &   needs_autoescape=True autoescape=None esc(...) [2]    return mark_safe(...)
# ==================== ===================== =============== =============== =====================
#
# [1] Types of string passed to a template code:
#     1. Raw str or unicode. They're escaped on output if auto-escaping is in effect and presented
#        unchanged, otherwise
#     2. Already marker as safe (SafeBytes/Text, base: SafeData) commonly used for output that
#        contains raw HTML to keep
#     3. Marked as needing escaping, always escaped on output, regardless in autoescape block or
#        not, EscapeBytes/Text
# [2]: esc = conditional_escape if autoescape else lambda x: x

try:
    from django.template.defaulttags import include_is_allowed as _include_is_allowed
except ImportError:
    def _include_is_allowed(filepath: str) -> bool:
        """
        Return whether including `filepath` is allowed (removed since Django 1.10).

        See commit 04ee4059d71dbc6aa029907e251360eaf00e11bb#diff-45fa5fdd90e8a31a18a1e55ec2f94fa3
        """
        return os.path.abspath(filepath).startswith(settings.STATIC_ROOT)

NUMERIC_TEST: Final[re.Pattern[str]] = re.compile(r'^\d+$')
LABEL_TO_CLASS: Final[dict[str, str]] = {
    'ERROR': 'label-important',
    'FAILURE': 'label-important',
    'PENDING': 'label-warning',
    'STARTED': 'label-info',
    'PROGRESS': 'label-info',
    'RETRY': 'label-warning',
    'REVOKED': 'label-inverse',
    'SUCCESS': 'label-success'
}
LABEL_TO_CLASS.update(getattr(settings, 'LABEL_TO_CLASS', {}))


@register.filter(is_safe=True)
def getattribute(value: Any, attribute: Any) -> Any:
    """
    Get an attribute of an object dynamically from a string name.

    Source : https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ object|getattribute:dynamic_string_var }}
    """
    if hasattr(value, str(attribute)):
        return getattr(value, attribute)
    if isinstance(value, collections.abc.Mapping) and attribute in value:
        return value[attribute]
    if NUMERIC_TEST.match(str(attribute)) and len(value) > int(attribute):
        return value[int(attribute)]
    return string_if_invalid


@register.filter(needs_autoescape=True, safe=True)
@stringfilter
def inline(filepath: str, msg: bool = True, *, autoescape: bool = True) -> str:
    """Inline the contents of a static file into the template output."""
    if filepath in (None, string_if_invalid):
        return string_if_invalid
    if _include_is_allowed(filepath):
        return Path(filepath).read_text(encoding='utf-8')
    if settings.DEBUG and msg:
        filepath_escaped = conditional_escape(filepath) if autoescape else filepath
        return _("[Didn't have permission to include file {0}]").format(filepath_escaped)
    return string_if_invalid


@register.filter(is_safe=True)
def rst_title(value: Any, level: Any) -> str:
    r"""
    Return a title formatted with reSTructuredtext markup.

    * level as number: (1, 2, 3, 4, 5)
    * level as text: ('document', 'subtitle', 'chapter', 'section', 'subsection')

    Output::

        'Document Title'|rst_title:'document' -> ==============\nDocument Title\n==============\n
        'My Subtitle'|rst_title:'subtitle' -> -----------\nMy Subtitle\n-----------\n

    Source: https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ 'My chapter'|rst_title:'chapter' }}
    """
    value, level = str(value), str(level)
    length = len(value)
    if level in {'1', 'document'}:
        return f"{'=' * length}{os.linesep}{value}{os.linesep}{'=' * length}{os.linesep}"
    if level in {'2', 'subtitle'}:
        return f"{'-' * length}{os.linesep}{value}{os.linesep}{'-' * length}{os.linesep}"
    if level in {'3', 'chapter'}:
        return f"{value}{os.linesep}{'=' * length}{os.linesep}"
    if level in {'4', 'section'}:
        return f"{value}{os.linesep}{'-' * length}{os.linesep}"
    if level in {'5', 'subsection'}:
        return f"{value}{os.linesep}{'~' * length}{os.linesep}"
    return string_if_invalid


@register.filter(is_safe=True)
def secs_to_time(value: float | None, defaults_to_zero: bool = False) -> datetime.time | str:
    """
    Return an instance of time, taking value as the number of seconds + microseconds
    (e.g. 10.3 = 10s 3000us).

    Output::

        83707.0035|secs_to_time|time:"H:i:s.u" -> 23:15:07.003500
        None|secs_to_time|time:"H:i:s.u"       -> (empty string)
        None|secs_to_time:True|time:"H:i:s.u"  -> 00:00:00.000000
    """
    if value is None:
        if defaults_to_zero:
            return _secs_to_time(0)
        return string_if_invalid
    return _secs_to_time(value)


@register.filter(needs_autoescape=True)
@stringfilter
def status_label(value: str, *, autoescape: bool | None = None, default: str = '') -> SafeString:
    """
    Return the status string represented as a span with a Twitter Bootstrap class.

    Output::

        'ERROR'|status_label -> <span class="label label-important">ERROR</span>

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ my_status_variable|status_label }}
    """
    esc = conditional_escape if autoescape else lambda x: x
    value = esc(value).upper()
    return mark_safe(f'<span class="label {LABEL_TO_CLASS.get(value, default)}">{value}</span>')


@register.filter(is_safe=True)
def timedelta(value: datetime.timedelta | float | None, digits: int = 0) -> str:
    """
    Return a string with representation of total seconds given timedelta or a number.

    Output::

        6316.9|timedelta -> 01:45:17
        datetime.timedelta(0, 6317)|timedelta -> 01:45:17
        datetime.timedelta(days=10, hours=2)|timedelta -> 10 days, 02:00:00
        datetime.timedelta(days=10, seconds=30.408)|timedelta -> 10 days, 00:00:30
        datetime.timedelta(days=10, seconds=30.408)|timedelta:2 -> 10 days, 00:00:30.45
        None|timedelta:10 -> (empty string)
        (empty string)|timedelta -> (empty string)
    """
    if value in (None, string_if_invalid):
        return string_if_invalid
    seconds = value.total_seconds() if hasattr(value, 'total_seconds') else float(value)
    return force_str(datetime.timedelta(seconds=round(seconds, digits))).replace('days', _('days'))


@register.filter
def verbose_name(instance: Any) -> str:
    """Return the verbose name (singular) of a model."""
    if instance in (None, string_if_invalid):
        return string_if_invalid
    return constants.DEFFERED_REGEX.sub('', force_str(instance._meta.verbose_name))


@register.filter
def verbose_name_plural(instance: Any) -> str:
    """Return the verbose name (plural) of a model."""
    if instance in (None, string_if_invalid):
        return string_if_invalid
    return constants.DEFFERED_REGEX.sub('', force_str(instance._meta.verbose_name))


# Tags ---------------------------------------------------------------------------------------------


class StaticPathNode(StaticNode):
    """Resolve a static file path using ``STATIC_ROOT`` instead of ``STATIC_URL``."""

    @classmethod
    def handle_simple(cls, path: str) -> str:
        """Return the absolute filesystem path for a static file."""
        return os.path.join(PrefixNode.handle_simple('STATIC_ROOT'), path)


@register.tag('static_abspath')
def static_abspath(parser, token):
    """
    Join the given path with the STATIC_ROOT setting.

    Usage::

        {% static path [as varname] %}

    Examples::

        {% static "myapp/css/base.css" %}
        {% static variable_with_path %}
        {% static "myapp/css/base.css" as admin_base_css %}
        {% static variable_with_path as varname %}

    """
    return StaticPathNode.handle_token(parser, token)
