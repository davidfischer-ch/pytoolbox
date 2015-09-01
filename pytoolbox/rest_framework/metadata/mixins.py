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

from rest_framework import serializers

from ... import module

_all = module.All(globals())


class ExcludeRelatedChoicesMixin(object):
    """Do not includes related fields to avoid having choices with hundreds instances."""

    related_fields = (serializers.RelatedField, serializers.ManyRelatedField)

    def get_field_info(self, field):
        if hasattr(field, 'choices') and isinstance(field, self.related_fields):
            field_class = field.__class__

            class HaveNoChoicesProxy(field_class):

                @property
                def choices(self):
                    raise AttributeError

            try:
                field.__class__ = HaveNoChoicesProxy
                return super(ExcludeRelatedChoicesMixin, self).get_field_info(field)
            finally:
                field.__class__ = field_class
        return super(ExcludeRelatedChoicesMixin, self).get_field_info(field)

__all__ = _all.diff(globals())
