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


class MultiTablesMixin(object):
    """Implements the base code for using multiple django-datatable-views powered tables."""

    multi_default = 'default'
    multi_datatables = ()
    request_name_key = 'datatable-name'

    def get_ajax_url(self, name=None):
        return (self.request.path + '?{0}={1}'.format(self.request_name_key, self.get_datatable_name(name)))

    def get_context_data(self, **kwargs):
        context = super(MultiTablesMixin, self).get_context_data(**kwargs)
        default_table = context.pop('datatable')
        context['datatables'] = [
            (name, label, (default_table if name == self.multi_default else self.get_datatable(name=name)))
            for name, label in self.multi_datatables
        ]
        return context

    def get_datatable(self, name=None):
        return self.get_datatable_structure(name=name)

    def get_datatable_name(self, name):
        return name or self.request.GET.get(self.request_name_key) or self.multi_default

    def get_datatable_structure(self, name=None):
        options = self._get_datatable_options()
        return self.datatable_structure_class(self.get_ajax_url(name=name), options, model=self.get_model())

    def get_queryset(self, name=None):
        qs = super(MultiTablesMixin, self).get_queryset()
        name = self.get_datatable_name(name)
        if name not in set(n for n, l in self.multi_datatables):
            return qs.none()  # Bad name, returns nothing!
        return getattr(self, 'get_{0}_queryset'.format(name))(qs)
