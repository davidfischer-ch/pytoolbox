# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
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
# Credits: https://gist.github.com/yahyaKacem/8170675
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import re

__all__ = ('ALL_CAP_REGEX', 'FIRST_CAP_REGEX', 'camel_to_dash', 'camel_to_snake', 'dash_to_camel', 'snake_to_camel')

ALL_CAP_REGEX = re.compile(r'([a-z0-9])([A-Z])')
FIRST_CAP_REGEX = re.compile(r'(.)([A-Z][a-z]+)')


def camel_to_dash(string):
    """Convert camelCase to dashed-case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1-\2', string)
    dashed_case_str = ALL_CAP_REGEX.sub(r'\1-\2', sub_string).lower()
    return dashed_case_str.replace('--', '-')


def camel_to_snake(string):
    """Convert camelCase to snake_case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1_\2', string)
    snake_cased_str = ALL_CAP_REGEX.sub(r'\1_\2', sub_string).lower()
    return snake_cased_str.replace('__', '_')


def dash_to_camel(string):
    return _to_camel(string, '-')


def snake_to_camel(string):
    return _to_camel(string, '_')


def _to_camel(string, separator):
    components = string.split(separator)
    preffix = suffix = ''
    if components[0] == '':
        components = components[1:]
        preffix = separator
    if components[-1] == '':
        components = components[:-1]
        suffix = separator
    if len(components) > 1:
        camel_case_string = components[0].lower()
        for x in components[1:]:
            if x.isupper() or x.istitle():
                camel_case_string += x
            else:
                camel_case_string += x.title()
    else:
        camel_case_string = components[0]
    return preffix + camel_case_string + suffix
