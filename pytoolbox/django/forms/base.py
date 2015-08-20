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

from django.utils.functional import cached_property

from ..models import utils
from ... import module

_all = module.All(globals())


class SerializedInstanceForm(object):

    def __init__(self, **kwargs):
        self.app_label = kwargs['app_label']
        self.model = kwargs['model']
        self.pk = kwargs['pk']

    @classmethod
    def serialize(cls, instance):
        return utils.get_content_type_dict(instance)

    @cached_property
    def instance(self):
        return utils.get_instance(self.app_label, self.model, self.pk)

    def is_valid(self):
        try:
            return bool(self.instance)
        except:
            return False

_all = module.All(globals())
