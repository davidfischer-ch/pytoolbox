# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

from copy import copy
from django.forms import fields
from django.forms.util import ErrorList
from .widgets import CalendarDateInput, ClockTimeInput
from ..encoding import to_bytes


class HelpTextToPlaceholderMixin(object):
    u"""Update the widgets of the form to copy (and remove) the field's help text to the widget's placeholder."""

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
                field.widget.attrs[u'placeholder'] = field.help_text
                if self.placeholder_remove_help_text:
                    field.help_text = None


class ModelBasedFormCleanupMixin(object):
    u"""
    Make possible the cleanup of the form by the model through a class method called ``clean_form``.
    Useful to cleanup the form based on complex conditions, e.g. if two fields are inter-related (start/end dates, ...).
    """

    def clean(self):
        super(ModelBasedFormCleanupMixin, self).clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


class UpdateWidgetAttributeMixin(object):
    u"""
    Update the widgets of the form based on a set of rules applied depending of the form field's class.
    The rules can change the class of the widget and/or update the attributes of the widget with
    :function:`update_widget_attributes`.
    """

    #: Set of rules linking the form field's class to the replacement class and the attributes update list.
    widgets_rules = {
        fields.DateField: [CalendarDateInput, {u'class': u'+dateinput +input-small'}],
        fields.TimeField: [ClockTimeInput,    {u'class': u'+timeinput +input-small'}],
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
                update_widget_attributes(field.widget, self.widgets_common_attrs)
            # May update widget attributes with rules-based attributes
            if updates and updates[1]:
                update_widget_attributes(field.widget, updates[1])
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass


def update_widget_attributes(widget, updates):
    u"""
    Update attributes of a ``widget`` with content of ``updates`` handling classes addition [+], removal [-] and
    toggle [^].

    **Example usage**

    >>> from nose.tools import assert_equal
    >>> widget = type('', (), {})
    >>> widget.attrs = {u'class': u'mondiale'}
    >>> update_widget_attributes(widget, {u'class': u'+pigeon +pigeon +voyage -mondiale -mondiale, ^voyage ^voyageur'})
    >>> assert_equal(widget.attrs, {u'class': u'pigeon voyageur'})
    >>> update_widget_attributes(widget, {u'class': '+le', u'cols': 100})
    >>> assert_equal(widget.attrs, {u'class': u'le pigeon voyageur', u'cols': 100})
    """
    updates = copy(updates)
    if u'class' in updates:
        class_set = set([c for c in widget.attrs.get(u'class', u'').split(u' ') if c])
        for cls in set([c for c in updates[u'class'].split(u' ') if c]):
            operation, cls = cls[0], cls[1:]
            if operation == u'+' or (operation == u'^' and not cls in class_set):
                class_set.add(cls)
            elif operation in (u'-', u'^'):
                class_set.discard(cls)
            else:
                raise ValueError(to_bytes(
                    u'updates must be a valid string containing "<op>class <op>..." with op in [+-^].'))
        widget.attrs[u'class'] = u' '.join(sorted(class_set))
        del updates[u'class']
    widget.attrs.update(updates)


def conditional_required(form, required_dict, data=None, cleanup=False):
    u"""Toggle requirement of some fields based on a dictionary with 'field name' -> 'required boolean'."""
    data = data or form.cleaned_data
    for name, value in data.iteritems():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList([u'This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data


def validate_start_end(form, data=None, start_name=u'start_date', end_name=u'end_date'):
    u"""Check that the field containing the value of the start field (time, ...) is not bigger (>) than the stop."""
    data = data or form.cleaned_data
    start, end = data[start_name], data[end_name]
    if start and end and start > end:
        form._errors[end_name] = ErrorList([u'The {0} cannot be before the {1}.'.format(
                                           start_name.replace(u'_', u' '), end_name.replace(u'_', u' '))])


def set_disabled(form, field_name, value=False):
    u"""Toggle the disabled attribute of a form's field."""
    if value:
        form.fields[field_name].widget.attrs[u'disabled'] = True
    else:
        try:
            del form.fields[field_name].widget.attrs[u'disabled']
        except:
            pass
