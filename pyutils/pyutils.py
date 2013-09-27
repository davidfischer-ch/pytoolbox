# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#  Description    : Toolbox for Python scripts
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pyutils Project.
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
# Retrieved from https://github.com/davidfischer-ch/pyutils.git

import uuid


class DBModel(object):
    u"""
    Implement an ``object`` with a method called ``to_dict`` that returns a ``dict`` containing
    fields and properties specified in ``DICT_FIELDS`` and ``DICT_PROPERTIES``.

    It is useful to inherit your *ming* or *sqlalchemy* models from the ``DBModel``class to control
    which fields and properties you want to include into the ``dict`` you may JSONify.
    """
    DICT_FIELDS = DICT_PROPERTIES = None

    def to_dict(self, include_properties=False, load_fields=False):
        u"""
        Returns a ``dict`` containing fields and properties of the object.
        This method handles recursion (e.g. a field may be a DBModel itself ...).

        :param include_properties: Set to True to include properties listed into DICT_PROPERTIES.
        :type include_properties: bool
        :param load_fields: Set to True to load value of any foreign model.
        :type load_fields: bool
        """
        user_dict = {}
        if self.DICT_FIELDS is not None:
            for field in self.DICT_FIELDS:
                if load_fields and len(field) > 3 and u'_id' in field:
                    field = field.replace(u'_id', u'')
                value = getattr(self, field)
                if isinstance(value, DBModel):
                    value = value.to_dict(include_properties, load_fields)
                user_dict[field] = value
        if include_properties and self.DICT_PROPERTIES is not None:
            for p in self.DICT_PROPERTIES:
                user_dict[p] = getattr(self, p)
        return user_dict


def sorted_dict(dictionary):
    return sorted(dictionary.items(), key=lambda x: x[0])


UUID_ZERO = unicode(uuid.UUID(u'{00000000-0000-0000-0000-000000000000}'))
