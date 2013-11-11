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

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = template.Library()

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


@register.filter(needs_autoescape=True)
@stringfilter
def status_label(value, autoescape=None, default=u''):
    u"""
    Return the status string represented as a span with a Twitter Bootstrap class.

    Output::

        'ERROR'|status_label -> <span class="label label-important">ERROR</span>

    **Example usage**

    In template::

        {% load status_label %}
        {{ my_status_variable|status_label }}
    """
    esc = conditional_escape if autoescape else lambda x: x
    value = esc(value).upper()
    return mark_safe(u'<span class="label {0}">{1}</span>'.format(LABEL_TO_CLASS.get(value, default), value))
