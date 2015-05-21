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

from ...django import forms

__all__ = ('SerializeStepInstanceMixin', )


class SerializeStepInstanceMixin(object):

    serialized_instance_form_class = forms.SerializedInstanceForm
    serialized_instances_key = 'serialized-instances'

    @property
    def serialized_instances(self):
        try:
            return self.storage.extra_data[self.serialized_instances_key]
        except KeyError:
            value = self.storage.extra_data[self.serialized_instances_key] = {}
            return value

    def serialize_step_instance(self, form, step=None):
        self.serialized_instances[step or self.steps.current] = \
            self.serialized_instance_form_class.serialize(form.save())

    # WizardView "Standard Methods"

    def get_form(self, step=None, *args, **kwargs):
        if step is None:
            step = self.steps.current
        if step in self.serialized_instances.keys():
            self.form_list[step] = self.serialized_instance_form_class
        return super(SerializeStepInstanceMixin, self).get_form(step, *args, **kwargs)

    def get_form_kwargs(self, step):
        form_kwargs = super(SerializeStepInstanceMixin, self).get_form_kwargs(step)
        serialized_instance = self.serialized_instances.get(step, None)
        if serialized_instance:
            form_kwargs.update(serialized_instance)
        return form_kwargs
