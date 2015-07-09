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
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import module
from ..encoding import string_types
from ..regex import UUID_REGEX

_all = module.All(globals())

INT_PK = r'(?P<pk>\d+)'
UUID_PK = r'(?P<pk>%s)' % UUID_REGEX


def get_named_patterns():
    """Returns a generator containing (pattern name, pattern) tuples."""
    from django.core.urlresolvers import get_resolver
    return ((k, v[0][0][0]) for k, v in get_resolver(None).reverse_dict.items() if isinstance(k, string_types))

__all__ = _all.diff(globals())
