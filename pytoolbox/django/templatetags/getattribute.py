# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
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

import re
from django import template
from django.conf import settings


numeric_test = re.compile('^\d+$')
register = template.Library()


def getattribute(value, attribute):
    u"""
    Gets an attribute of an object dynamically from a string name.

    Source : https://snipt.net/Fotinakis/django-template-tag-for-dynamic-attribute-lookups/
    """
    if hasattr(value, str(attribute)):
        return getattr(value, attribute)
    elif hasattr(value, u'has_key') and value.has_key(attribute):
        return value[attribute]
    elif numeric_test.match(str(attribute)) and len(value) > int(attribute):
        return value[int(attribute)]
    else:
        return settings.TEMPLATE_STRING_IF_INVALID

register.filter(u'getattribute', getattribute)

# Then, in template:
# {% load getattribute %}
# {{ object|getattribute:dynamic_string_var }}
