# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

__all__ = ('TIME_REGEX_PARTS', 'findall_partial')

TIME_REGEX_PARTS = ['[0-2]', '[0-9]', ':', '[0-5]', '[0-9]', ':', '[0-5]', '[0-9]']


def findall_partial(string, regex_parts):
    """
    TODO

    **Example usage**

    >>> list(''.join(r) for i, r in findall_partial('12:15:2', TIME_REGEX_PARTS))
    ['12:15:2[0-9]']
    >>> list(''.join(r) for i, r in findall_partial('18:2', TIME_REGEX_PARTS))
    ['18:2[0-9]:[0-5][0-9]', '[0-2][0-9]:18:2[0-9]']
    >>> list(''.join(r) for i, r in findall_partial('59:1', TIME_REGEX_PARTS))
    ['[0-2][0-9]:59:1[0-9]']
    >>> set(''.join(r) for i, r in findall_partial(':', TIME_REGEX_PARTS))
    {'[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'}
    """
    length = len(string)
    for index in range(0, len(regex_parts) - length + 1):
        regex = regex_parts[index:index+length]
        match = re.search(''.join(regex), string)
        if match:
            regex = regex_parts[:]
            regex[index:index+length] = string
            yield index, regex
