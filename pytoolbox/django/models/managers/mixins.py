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

from .... import module

_all = module.All(globals())


class CreateModelMethodMixin(object):

    def create(self, *args, **kwargs):
        if hasattr(self.model, 'create'):
            return self.model.create(*args, **kwargs)
        return super(CreateModelMethodMixin, self).create(*args, **kwargs)
    create.alters_data = True


class RelatedModelMixin(object):

    def get_related_manager(self, field):
        return self.get_related_model(field)._default_manager

    def get_related_model(self, field):
        return self.model._meta.get_field(field).related_model

__all__ = _all.diff(globals())
