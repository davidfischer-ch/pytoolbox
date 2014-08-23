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

from datetime import datetime

__all__ = ('Metadata', )


class Metadata(object):

    def __init__(self, path):
        from gi.repository import GExiv2
        self._m = GExiv2.Metadata()
        self._m.open_path(path)

    def __getitem__(self, key):
        return self._m[key]

    def get(self, key):
        value = self._m.get(key, default=None)
        return str(value) if value else None

    def get_date(self, key):
        value = self.get(key)
        try:
            return datetime.strptime(value.replace(': ', ':0'), '%Y:%m:%d %H:%M:%S') if value else None
        except ValueError:
            if value == '0000:00:00 00:00:00':
                return None
            raise

    def get_float(self, key):
        value = self.get(key)
        if not value:
            return None
        num, denom = value.split('/')
        return float(num) / float(denom)

    def get_int(self, key):
        value = self.get(key)
        return int(value) if value else None
