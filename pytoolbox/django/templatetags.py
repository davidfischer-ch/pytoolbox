# -*- encoding: utf-8 -*-

"""
Pytoolbox's Template tag and filters.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, os, re

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.templatetags.static import PrefixNode, StaticNode
from django.utils.html import conditional_escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pytoolbox import humanize, module
from pytoolbox.datetime import secs_to_time as _secs_to_time
from pytoolbox.encoding import to_unicode
from pytoolbox.private import _parse_kwargs_string

from .core import constants

_all = module.All(globals())

try:
    from django.template.defaulttags import include_is_allowed as _include_is_allowed
except ImportError:
    def _include_is_allowed(filepath):
        """
        Removed since Django 1.10
        See commit 04ee4059d71dbc6aa029907e251360eaf00e11bb#diff-45fa5fdd90e8a31a18a1e55ec2f94fa3
        """
        return os.path.abspath(filepath).startswith(settings.STATIC_ROOT)

string_if_invalid = ''  # Official default value
try:  # Django >= 1.8
    string_if_invalid = settings.TEMPLATES['OPTIONS']['string_if_invalid']
except:
    try:  # Django < 1.8
        string_if_invalid = settings.TEMPLATE_STRING_IF_INVALID
    except:
        pass  # Use default


# ====================   =====================   ===============   ===============   =====================
# description            decorator               arguments         input             output
# ====================   =====================   ===============   ===============   =====================
# only accept string     @stringfilter           -                 is a string [1]   return ...
# do not add < > ' " &   is_safe=True            -                 of any type       return ...
# add HTML < > ' " &     needs_autoescape=True   autoescape=None   esc(...) [2]      return mark_safe(...)
# ====================   =====================   ===============   ===============   =====================
#
# [1] Types of string passed to a template code:
#     1. Raw str or unicode. They’re escaped on output if auto-escaping is in effect and presented unchanged, otherwise
#     2. Already marker as safe (SafeBytes/Text, base: SafeData) commonly used for output that contains raw HTML to keep
#     3. Marked as needing escaping, always escaped on output, regardless in autoescape block or not, EscapeBytes/Text
# [2]: esc = conditional_escape if autoescape else lambda x: x

register = template.Library()

NUMERIC_TEST = re.compile('^\d+$')
LABEL_TO_CLASS = {
    'ERROR':    'label-important',
    'FAILURE':  'label-important',
    'PENDING':  'label-warning',
    'STARTED':  'label-info',
    'PROGRESS': 'label-info',
    'RETRY':    'label-warning',
    'REVOKED':  'label-inverse',
    'SUCCESS':  'label-success'
}
LABEL_TO_CLASS.update(getattr(settings, 'LABEL_TO_CLASS', {}))


@register.filter(is_safe=True)
def getattribute(value, attribute):
    """
    Gets an attribute of an object dynamically from a string name.

    Source : https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ object|getattribute:dynamic_string_var }}
    """
    if hasattr(value, str(attribute)):
        return getattr(value, attribute)
    elif hasattr(value, 'has_key') and value.has_key(attribute):
        return value[attribute]
    elif NUMERIC_TEST.match(str(attribute)) and len(value) > int(attribute):
        return value[int(attribute)]
    return string_if_invalid


@register.filter(needs_autoescape=True, safe=True)
@stringfilter
def inline(filepath, msg=True, autoescape=True):
    if filepath in (None, string_if_invalid):
        return string_if_invalid
    if _include_is_allowed(filepath):
        return open(filepath, encoding='utf-8').read()
    if settings.DEBUG and msg:
        filepath_escaped = conditional_escape(filepath) if autoescape else filepath
        return _("[Didn't have permission to include file {0}]").format(filepath_escaped)
    return string_if_invalid


@register.filter(is_safe=True)
def naturalbitrate(bps, kwargs_string=None):
    """
    Return a human readable representation of a bit rate taking `bps` as the rate in bits/s.
    See documentation of :func:`pytoolbox.humanize.naturalbitrate` for further examples.

    Output::

        16487211.33|naturalbitrate -> 16.5 Mb/s
        16487211.33|naturalbitrate:'format={value:.0f} {unit}' -> 16 Mb/s
        16487211.33|naturalbitrate:'format={sign}{value:.0f} {unit}; scale=1' -> 16487 kb/s
        -16487211.33|naturalbitrate:'format={sign}{value:.0f} {unit}' -> -16 Mb/s
        None|naturalbitrate -> (empty string)
        (empty string)|naturalbitrate -> (empty string)
    """
    if bps in (None, string_if_invalid):
        return string_if_invalid
    return humanize.naturalbitrate(
        bps, **_parse_kwargs_string(kwargs_string, format=str, scale=int))


@register.filter(is_safe=True)
def naturalfilesize(the_bytes, kwargs_string=None):
    """
    Return a human readable representation of a *file* size taking `the_bytes` as the size in bytes.
    See documentation of :func:`pytoolbox.humanize.naturalfilesize` for further examples.

    Output::

        16487211.33|naturalfilesize -> 15.7 MB
        16487211.33|naturalfilesize:'system=si' -> 16.5 MiB
        16487211.33|naturalfilesize:'format={value:.0f} {unit}; system=gnu' -> 16 M
        16487211.33|naturalfilesize:'format={sign}{value:.0f} {unit}; scale=1' -> 16101 kB
        -16487211.33|naturalfilesize:'format={sign}{value:.0f} {unit}' -> -16 MB
        None|naturalfilesize -> (empty string)
        (empty string)|naturalfilesize -> (empty string)
    """
    if the_bytes in (None, string_if_invalid):
        return string_if_invalid
    return humanize.naturalfilesize(
        the_bytes, **_parse_kwargs_string(kwargs_string, format=str, scale=int, system=str))


@register.filter(is_safe=True)
def rst_title(value, level):
    """
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
    value, level = to_unicode(value), to_unicode(level)
    length = len(value)
    if level in ('1', 'document'):
        return '{1}{0}{2}{0}{3}{0}'.format(os.linesep, '=' * length, value, '=' * length)
    elif level in ('2', 'subtitle'):
        return '{1}{0}{2}{0}{3}{0}'.format(os.linesep, '-' * length, value, '-' * length)
    elif level in ('3', 'chapter'):
        return '{1}{0}{2}{0}'.format(os.linesep, value, '=' * length)
    elif level in ('4', 'section'):
        return '{1}{0}{2}{0}'.format(os.linesep, value, '-' * length)
    elif level in ('5', 'subsection'):
        return '{1}{0}{2}{0}'.format(os.linesep, value, '~' * length)
    return string_if_invalid


@register.filter(is_safe=True)
def secs_to_time(value, defaults_to_zero=False):
    """
    Return an instance of time, taking value as the number of seconds + microseconds
    (e.g. 10.3 = 10s 3000us).

    Output::

        83707.0035|secs_to_time|time:"H:i:s.u" -> 23:15:07.003500
        None|secs_to_time|time:"H:i:s.u"       -> (empty string)
        None|secs_to_time:True|time:"H:i:s.u"  -> 00:00:00.000000
    """
    value = _secs_to_time(value, defaults_to_zero=defaults_to_zero)
    return value if value is not None else string_if_invalid


@register.filter(needs_autoescape=True)
@stringfilter
def status_label(value, autoescape=None, default=''):
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
    return mark_safe('<span class="label {0}">{1}</span>'.format(
        LABEL_TO_CLASS.get(value, default), value))


@register.filter(is_safe=True)
def timedelta(value, digits=0):
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
    return force_text(datetime.timedelta(seconds=round(seconds, digits))).replace('days', _('days'))


@register.filter
def verbose_name(instance):
    """Return the verbose name (singular) of a model."""
    if instance in (None, string_if_invalid):
        return string_if_invalid
    return constants.DEFFERED_REGEX.sub('', force_text(instance._meta.verbose_name))


@register.filter
def verbose_name_plural(instance):
    """Return the verbose name (plural) of a model."""
    if instance in (None, string_if_invalid):
        return string_if_invalid
    return constants.DEFFERED_REGEX.sub('', force_text(instance._meta.verbose_name))


# TAGS ---------------------------------------------------------------------------------------------

class StaticPathNode(StaticNode):

    @classmethod
    def handle_simple(cls, path):
        return os.path.join(PrefixNode.handle_simple('STATIC_ROOT'), path)


@register.tag('static_abspath')
def static_abspath(parser, token):
    """
    Joins the given path with the STATIC_ROOT setting.

    Usage::

        {% static path [as varname] %}

    Examples::

        {% static "myapp/css/base.css" %}
        {% static variable_with_path %}
        {% static "myapp/css/base.css" as admin_base_css %}
        {% static variable_with_path as varname %}

    """
    return StaticPathNode.handle_token(parser, token)


__all__ = _all.diff(globals())
