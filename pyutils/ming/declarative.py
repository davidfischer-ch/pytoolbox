#!/usr/bin/env python
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

from ming.odm.declarative import MappedClass


class MappedClassWithDict(MappedClass):
    u"""
    Implement a ``MappedClass`` with a method called ``to_dict`` that returns a ``dict`` containing
    fields and properties specified in ``DICT_FIELDS`` and ``DICT_PROPERTIES``.
    """
    DICT_FIELDS = DICT_PROPERTIES = None

    def to_dict(self, include_properties=False, load_fields=False):
        user_dict = {}
        if self.DICT_FIELDS is not None:
            for field in self.DICT_FIELDS:
                if load_fields and len(field) > 3 and '_id' in field:
                    field = field.replace('_id', '')
                value = getattr(self, field)
                if isinstance(value, MappedClassWithDict):
                    value = value.to_dict(include_properties, load_fields)
                user_dict[field] = value
        if include_properties and self.DICT_PROPERTIES is not None:
            for p in self.DICT_PROPERTIES:
                user_dict[p] = getattr(self, p)
        return user_dict
