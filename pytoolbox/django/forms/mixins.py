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

from django.forms import fields
from . import utils, widgets

__all__ = (
    'HelpTextToPlaceholderMixin', 'MapErrorsMixin', 'ModelBasedFormCleanupMixin', 'RequestMixin',
    'UpdateWidgetAttributeMixin'
)


class HelpTextToPlaceholderMixin(object):
    """Update the widgets of the form to copy (and remove) the field's help text to the widget's placeholder."""

    #: Add a placeholder to the type of fields listed here.
    placeholder_fields = (
        fields.CharField, fields.DateField, fields.DateTimeField, fields.DecimalField, fields.EmailField,
        fields.FloatField, fields.IntegerField, fields.RegexField, fields.SlugField, fields.TimeField
    )
    #: Remove the help text after having copied it to the placeholder.
    placeholder_remove_help_text = True

    def __init__(self, *args, **kwargs):
        super(HelpTextToPlaceholderMixin, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            if field and isinstance(field, self.placeholder_fields):
                self.set_placeholder(name, field)

    def set_placeholder(self, name, field):
        field.widget.attrs['placeholder'] = field.help_text
        if self.placeholder_remove_help_text:
            field.help_text = None


class MapErrorsMixin(object):
    """Map errors based on field name. Mandatory when the form contains a field from a model named differently."""

    errors_map = {}

    def add_error(self, field, error):
        field = self.errors_map.get(field, field)
        return super(MapErrorsMixin, self).add_error(field, error)


class ModelBasedFormCleanupMixin(object):
    """
    Make possible the cleanup of the form by the model through a class method called ``clean_form``.
    Useful to cleanup the form based on complex conditions, e.g. if two fields are inter-related (start/end dates, ...).
    """

    def clean(self):
        super(ModelBasedFormCleanupMixin, self).clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


class RequestMixin(object):
    """
    Accept request as a optional (default: None) argument of the constructor and set it as an attribute of the object.
    """

    def __init__(self, request=None, **kwargs):
        super(RequestMixin, self).__init__(**kwargs)
        self.request = request


class UpdateWidgetAttributeMixin(object):
    """
    Update the widgets of the form based on a set of rules applied depending of the form field's class.
    The rules can change the class of the widget and/or update the attributes of the widget with
    :function:`update_widget_attributes`.
    """

    #: Set of rules linking the form field's class to the replacement class and the attributes update list.
    widgets_rules = {
        fields.DateField: [widgets.CalendarDateInput, {'class': '+dateinput +input-small'}],
        fields.TimeField: [widgets.ClockTimeInput,    {'class': '+timeinput +input-small'}],
    }
    #: Attributes that are applied to all widgets of the form
    widgets_common_attrs = {}

    def __init__(self, *args, **kwargs):
        super(UpdateWidgetAttributeMixin, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            updates = self.widgets_rules.get(field.__class__)
            # May Update widget class with rules-based replacement class
            if updates and updates[0]:
                field.widget = updates[0]()
            # May update widget attributes with common attributes
            if self.widgets_common_attrs:
                utils.update_widget_attributes(field.widget, self.widgets_common_attrs)
            # May update widget attributes with rules-based attributes
            if updates and updates[1]:
                utils.update_widget_attributes(field.widget, updates[1])
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass
