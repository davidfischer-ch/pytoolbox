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


register = template.Library()


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

        {% load rst_title %}
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

register.filter(u'rst_title', rst_title)
