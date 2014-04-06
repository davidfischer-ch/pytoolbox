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

import hashlib
from .encoding import string_types


def githash(data, encoding=u'utf-8'):
    u"""
    Return the blob of some data.

    This is how Git calculates the SHA1 for a file (or, in Git terms, a "blob")::

        sha1('blob ' + filesize + '\0' + data)

    .. seealso::

        http://stackoverflow.com/questions/552659/assigning-git-sha1s-without-git

    **Example usage**

    >>> print(githash(u''))
    e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
    >>> print(githash(u'give me some hash please'))
    abdd1818289725c072eff0f5ce185457679650be
    >>> print(githash(u'et ça fonctionne !\\n'))
    91de5baf6aaa1af4f662aac4383b27937b0e663d
    """
    data_bytes = data.encode(encoding) if isinstance(data, string_types) else data
    s = hashlib.sha1()
    s.update((u'blob %d\0' % len(data_bytes)).encode(u'utf-8'))
    s.update(data_bytes)
    return s.hexdigest()
