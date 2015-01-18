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

__all__ = ('TIME_REGEX_PARTS', 'UUID_REGEX', 'embed_in_regex', 'findall_partial')

TIME_REGEX_PARTS = ['[0-2]', '[0-9]', ':', '[0-5]', '[0-9]', ':', '[0-5]', '[0-9]']
UUID_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


def embed_in_regex(string, regex_parts, index, as_string=True):
    """
    **Example usage**

    >>> from nose.tools import eq_

    >>> eq_(embed_in_regex('L', ['[a-z]', '[a-z]'], 0), (0, 'L[a-z]'))
    >>> eq_(embed_in_regex('L', ['[a-z]', '[a-z]'], 1), (1, '[a-z]L'))
    >>> eq_(embed_in_regex('L', ['[a-z]', '[a-z]'], 1, as_string=False), (1, ['[a-z]', 'L']))
    """
    regex = regex_parts[:]
    regex[index:index + len(string)] = string
    return index, ''.join(regex) if as_string else regex


def findall_partial(string, regex_parts):
    """
    **Example usage**

    >>> from nose.tools import eq_
    >>> result = [i for s, r, i in findall_partial(':', TIME_REGEX_PARTS)]
    >>> eq_(result, [2, 5])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('12:15:2', TIME_REGEX_PARTS)]
    >>> eq_(result, [(0, '12:15:2[0-9]')])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('18:2', TIME_REGEX_PARTS)]
    >>> eq_(result, [(0, '18:2[0-9]:[0-5][0-9]'), (3, '[0-2][0-9]:18:2[0-9]')])
    >>> result = [embed_in_regex(s, r, i) for s, r, i in findall_partial('59:1', TIME_REGEX_PARTS)]
    >>> eq_(result, [(3, '[0-2][0-9]:59:1[0-9]')])
    """
    for index in range(0, len(regex_parts) - len(string) + 1):
        regex = regex_parts[index:index + len(string)]
        match = re.search(''.join(regex), string)
        if match:
            yield string, regex_parts, index
