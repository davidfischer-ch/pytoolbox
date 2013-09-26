# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import hashlib, sys

if sys.version_info[0] < 3:
    def to_bytes(string):
        return string
else:
    def to_bytes(string):
        return bytes(string, u'utf-8')

def githash(data):
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
    """
    s = hashlib.sha1()
    s.update(to_bytes(u'blob {0}\0'.format(len(data))))
    s.update(to_bytes(data))
    return s.hexdigest()
