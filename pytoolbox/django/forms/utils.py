# -*- encoding: utf-8 -*-

"""
Some utilities related to the forms.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import copy

from django.contrib import messages
from django.forms.utils import ErrorList

from pytoolbox import module
from pytoolbox.encoding import to_bytes

_all = module.All(globals())


def conditional_required(form, required_dict, data=None, cleanup=False):
    """
    Toggle requirement of some fields based on a dictionary with 'field name' -> 'required boolean'.
    """
    data = data or form.cleaned_data
    for name, value in data.iteritems():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList(['This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data


def get_instance(form, field_name, request, msg=None):
    """
    Return the instance if the `form` is valid, or try to get it from database.
    Return None if not found and add an error message if set.
    """
    if form.is_valid():
        return form.cleaned_data[field_name]
    queryset = form.fields[field_name].queryset
    try:
        return queryset.get(pk=form.data[form.add_prefix(field_name)])
    except (KeyError, queryset.model.DoesNotExist):
        if msg:
            messages.error(request, msg)


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
    Update attributes of a `widget` with content of `updates` handling classes addition [+],
    removal [-] and toggle [^].

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> widget = type(str(''), (), {})
    >>> widget.attrs = {'class': 'mondiale'}
    >>> update_widget_attributes(
    ...     widget, {'class': '+pigeon +pigeon +voyage -mondiale -mondiale, ^voyage ^voyageur'})
    >>> asserts.dict_equal(widget.attrs, {'class': 'pigeon voyageur'})
    >>> update_widget_attributes(widget, {'class': '+le', 'cols': 100})
    >>> asserts.dict_equal(widget.attrs, {'class': 'le pigeon voyageur', 'cols': 100})
    """
    updates = copy(updates)
    if 'class' in updates:
        class_set = set([c for c in widget.attrs.get('class', '').split(' ') if c])
        for cls in set([c for c in updates['class'].split(' ') if c]):
            operation, cls = cls[0], cls[1:]
            if operation == '+' or (operation == '^' and cls not in class_set):
                class_set.add(cls)
            elif operation in ('-', '^'):
                class_set.discard(cls)
            else:
                raise ValueError(to_bytes(
                    'updates must be a valid string with "<op>class <op>..." with op in [+-^].'))
        widget.attrs['class'] = ' '.join(sorted(class_set))
        del updates['class']
    widget.attrs.update(updates)


def validate_start_end(form, data=None, start_name='start_date', end_name='end_date'):
    """
    Check that the field containing the value of the start field (time, ...) is not bigger (>) than
    the stop.
    """
    data = data or form.cleaned_data
    start, end = data[start_name], data[end_name]
    if start and end and start > end:
        form._errors[end_name] = ErrorList([
            'The {0} cannot be before the {1}.'.format(
                start_name.replace('_', ' '), end_name.replace('_', ' '))
        ])


__all__ = _all.diff(globals())
