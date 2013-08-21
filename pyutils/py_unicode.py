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

import sys
from codecs import open
from kitchen.text.converters import getwriter


# http://pythonhosted.org/kitchen/unicode-frustrations.html
def configure_unicode(encoding=u'utf-8'):
    u"""
    It is crucial to raise exceptions helped by :mod:`kitchen` ::

        from kitchen.text.converters import to_bytes
        configure_unicode()
        raise NotImplementedError(to_bytes(u'Saluté'))
    """
    sys.stdout = getwriter(encoding)(sys.stdout)
    sys.stderr = getwriter(encoding)(sys.stderr)


def csv_reader(filename, delimiter=u';', quotechar=u'"', encoding=u'utf-8'):
    u"""
    Yield the content of a CSV file.
    """
    with open(filename, u'r', encoding) as f:
        for line in f.readlines():
            line = line.strip()
            yield [cell for cell in line.split(delimiter)]
    #import csv
    #reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
    #for row in reader:
    #    yield [cell for cell in row]
        #yield [unicode(cell, 'utf-8').encode('utf-8') for cell in row]
