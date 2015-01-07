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

from copy import copy
from django.forms.util import ErrorList
from ...encoding import to_bytes

__all__ = ('conditional_required', 'set_disabled', 'update_widget_attributes', 'validate_start_end')


def conditional_required(form, required_dict, data=None, cleanup=False):
    """Toggle requirement of some fields based on a dictionary with 'field name' -> 'required boolean'."""
    data = data or form.cleaned_data
    for name, value in data.iteritems():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList(['This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data


def set_disabled(form, field_name, value=False):
    """Toggle the disabled attribute of a form's field."""
    if value:
        form.fields[field_name].widget.attrs['disabled'] = True
    else:
        try:
            del form.fields[field_name].widget.attrs['disabled']
        except:
            pass


def update_widget_attributes(widget, updates):
    """
    Update attributes of a `widget` with content of `updates` handling classes addition [+], removal [-] and
    toggle [^].

    **Example usage**

    >>> from nose.tools import eq_
    >>> widget = type('', (), {})
    >>> widget.attrs = {'class': 'mondiale'}
    >>> update_widget_attributes(widget, {'class': '+pigeon +pigeon +voyage -mondiale -mondiale, ^voyage ^voyageur'})
    >>> eq_(widget.attrs, {'class': 'pigeon voyageur'})
    >>> update_widget_attributes(widget, {'class': '+le', 'cols': 100})
    >>> eq_(widget.attrs, {'class': 'le pigeon voyageur', 'cols': 100})
    """
    updates = copy(updates)
    if 'class' in updates:
        class_set = set([c for c in widget.attrs.get('class', '').split(' ') if c])
        for cls in set([c for c in updates['class'].split(' ') if c]):
            operation, cls = cls[0], cls[1:]
            if operation == '+' or (operation == '^' and not cls in class_set):
                class_set.add(cls)
            elif operation in ('-', '^'):
                class_set.discard(cls)
            else:
                raise ValueError(to_bytes(
                    'updates must be a valid string containing "<op>class <op>..." with op in [+-^].'))
        widget.attrs['class'] = ' '.join(sorted(class_set))
        del updates['class']
    widget.attrs.update(updates)


def validate_start_end(form, data=None, start_name='start_date', end_name='end_date'):
    """Check that the field containing the value of the start field (time, ...) is not bigger (>) than the stop."""
    data = data or form.cleaned_data
    start, end = data[start_name], data[end_name]
    if start and end and start > end:
        form._errors[end_name] = ErrorList(['The {0} cannot be before the {1}.'.format(
                                           start_name.replace('_', ' '), end_name.replace('_', ' '))])
