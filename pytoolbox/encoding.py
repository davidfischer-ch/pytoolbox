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

import six, sys
from codecs import open

string_types = six.string_types

if sys.version_info[0] == 2:
    import kitchen.text.converters
    to_bytes = kitchen.text.converters.to_bytes

    # http://pythonhosted.org/kitchen/unicode-frustrations.html
    def configure_unicode(encoding='utf-8'):
        """Configure ``sys.stdout`` and ``sys.stderr`` to be in Unicode (Do nothing if Python 3)."""
        sys.stdout = kitchen.text.converters.getwriter(encoding)(sys.stdout)
        sys.stderr = kitchen.text.converters.getwriter(encoding)(sys.stderr)
else:
    def to_bytes(message):
        """Convert an Unicode message to bytes, useful for raising exceptions in Python 2.

        **Example usage**

        >>> configure_unicode()
        >>> raise NotImplementedError(to_bytes('Saluté'))
        Traceback (most recent call last):
            ...
        NotImplementedError: Saluté
        """
        return unicode(message)

    def configure_unicode(encoding='utf-8'):
        """Configure ``sys.stdout`` and ``sys.stderr`` to be in Unicode (Do nothing if Python 3)."""
        pass


def csv_reader(filename, delimiter=';', quotechar='"', encoding='utf-8'):
    """Yield the content of a CSV file."""
    with open(filename, 'r', encoding) as f:
        for line in f.readlines():
            line = line.strip()
            yield [cell for cell in line.split(delimiter)]
    #import csv
    #reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
    #for row in reader:
    #    yield [cell for cell in row]
        #yield [unicode(cell, 'utf-8').encode('utf-8') for cell in row]
