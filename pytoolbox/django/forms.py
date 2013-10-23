# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
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
from django.forms import ModelForm, fields
from django.forms.util import ErrorList
from .widgets import CalendarDateInput, ClockTimeInput


class SmartModelForm(ModelForm):

    # Attributes & replacement class applied depending of the form field's class
    rules = {  # class -> replacement class, attributes update list
        fields.DateField: [CalendarDateInput, {u'class': u'+dateinput +input-small'}],
        fields.TimeField: [ClockTimeInput,    {u'class': u'+timeinput +input-small'}],
    }

    common_attrs = {}  # Attributes that are applied to all widgets of the form

    def __init__(self, *args, **kwargs):
        super(SmartModelForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            updates = self.rules.get(field.__class__)
            # May Update widget class with rules-based replacement class
            if updates and updates[0]:
                field.widget = updates[0]()
            # May update widget attributes with common attributes
            if self.common_attrs:
                update_widget_attributes(field.widget, self.common_attrs)
            # May update widget attributes with rules-based attributes
            if updates and updates[1]:
                update_widget_attributes(field.widget, updates[1])
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass

    def clean(self):
        super(SmartModelForm, self).clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


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
                raise ValueError('updates must be a valid string containing "<op>class <op>..." with op in [+-^].')
        widget.attrs[u'class'] = u' '.join(sorted(class_set))
        del updates[u'class']
    widget.attrs.update(updates)


def conditional_required(form, required_dict, cleanup=False):
    data = form.cleaned_data
    for name, value in data.iteritems():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList([u'This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data


def set_disabled(form, field_name, value=False):
    if value:
        form.fields[field_name].widget.attrs[u'disabled'] = True
    else:
        try:
            del form.fields[field_name].widget.attrs[u'disabled']
        except:
            pass
