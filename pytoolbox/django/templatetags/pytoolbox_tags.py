# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import re, datetime
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

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


NUMERIC_TEST = re.compile('^\d+$')
LABEL_TO_CLASS = {
    u'ERROR':    u'label-important',
    u'FAILURE':  u'label-important',
    u'PENDING':  u'label-warning',
    u'STARTED':  u'label-info',
    u'PROGRESS': u'label-info',
    u'RETRY':    u'label-warning',
    u'REVOKED':  u'label-inverse',
    u'SUCCESS':  u'label-success'
}
LABEL_TO_CLASS.update(getattr(settings, u'LABEL_TO_CLASS', {}))


@register.filter(is_safe=True)
def getattribute(value, attribute):
    u"""
    Gets an attribute of an object dynamically from a string name.

    Source : https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ object|getattribute:dynamic_string_var }}
    """
    if hasattr(value, str(attribute)):
        return getattr(value, attribute)
    elif hasattr(value, u'has_key') and value.has_key(attribute):
        return value[attribute]
    elif NUMERIC_TEST.match(str(attribute)) and len(value) > int(attribute):
        return value[int(attribute)]
    return settings.TEMPLATE_STRING_IF_INVALID


@register.filter(is_safe=True)
def rst_title(value, level):
    u"""
    Return a title formatted with reSTructuredtext markup.

    level as number: (1, 2, 3, 4, 5)
    level as text: ('document', 'subtitle', 'chapter', 'section', 'subsection')

    Output::

        'Document Title'|rst_title:'document' -> ==============\nDocument Title\n==============\n
        'My Subtitle'|rst_title:'subtitle' -> -----------\nMy Subtitle\n-----------\n

    Source : https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/

    **Example usage**

    In template::

        {% load pytoolbox_tags %}
        {{ 'My chapter'|rst_title:'chapter' }}
    """
    value, level = unicode(value), unicode(level)
    length = len(value)
    if level in (u'1', u'document'):
        return u'{0}\n{1}\n{2}\n'.format(u'=' * length, value, u'=' * length)
    elif level in (u'2', u'subtitle'):
        return u'{0}\n{1}\n{2}\n'.format(u'-' * length, value, u'-' * length)
    elif level in (u'3', u'chapter'):
        return u'{0}\n{1}\n'.format(value, u'=' * length)
    elif level in (u'4', u'section'):
        return u'{0}\n{1}\n'.format(value, u'-' * length)
    elif level in (u'5', u'subsection'):
        return u'{0}\n{1}\n'.format(value, u'~' * length)
    return settings.TEMPLATE_STRING_IF_INVALID


@register.filter(is_safe=True)
def secs_to_time(value, defaults_to_zero=False):
    u"""
    Return an instance of time, taking value as the number of seconds + microseconds (e.g. 10.3 = 10s 3000us).

    Output::

        83707.0035|secs_to_time|time:"H:i:s.u" -> 23:15:07.003500
        None|secs_to_time|time:"H:i:s.u"       -> (nothing)
        None|secs_to_time:True|time:"H:i:s.u"  -> 00:00:00.000000
    """
    try:
        return (datetime.datetime.min + datetime.timedelta(seconds=float(value))).time()
    except (TypeError, ValueError):
        if defaults_to_zero and not value:
            return datetime.time(second=0)
        return settings.TEMPLATE_STRING_IF_INVALID


@register.filter(needs_autoescape=True)
@stringfilter
def status_label(value, autoescape=None, default=u''):
    u"""
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
    return mark_safe(u'<span class="label {0}">{1}</span>'.format(LABEL_TO_CLASS.get(value, default), value))
