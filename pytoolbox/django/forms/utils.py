"""
Some utilities related to the forms.
"""

from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from django.contrib import messages
from django.forms.utils import ErrorList

from pytoolbox import module

if TYPE_CHECKING:
    from django import forms
    from django.db import models
    from django.http import HttpRequest

_all = module.All(globals())


def conditional_required(
    form: forms.Form,
    required_dict: dict[str, bool | None],
    data: dict[str, object] | None = None,
    *,
    cleanup: bool = False,
) -> dict[str, object]:
    """
    Toggle requirement of some fields based on a dictionary with 'field name' -> 'required boolean'.
    """
    data = data or form.cleaned_data
    for name, value in data.items():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList(['This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data


def get_instance(
    form: forms.Form,
    field_name: str,
    request: HttpRequest,
    msg: str | None = None,
) -> models.Model | None:
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
        return None


def set_disabled(form: forms.Form, field_name: str, *, value: bool = False) -> None:
    """Toggle the disabled attribute of a form's field."""
    if value:
        form.fields[field_name].widget.attrs['disabled'] = True
    else:
        try:
            del form.fields[field_name].widget.attrs['disabled']
        except KeyError:
            pass


def update_widget_attributes(widget: forms.Widget, updates: dict[str, object]) -> None:
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
        class_set = {c for c in widget.attrs.get('class', '').split(' ') if c}
        for cls in {c for c in updates['class'].split(' ') if c}:
            operation, cls = cls[0], cls[1:]
            if operation == '+' or (operation == '^' and cls not in class_set):
                class_set.add(cls)
            elif operation in {'-', '^'}:
                class_set.discard(cls)
            else:
                raise ValueError(
                    'updates must be a valid string with "<op>class <op>..." with op in [+-^].',
                )
        widget.attrs['class'] = ' '.join(sorted(class_set))
        del updates['class']
    widget.attrs.update(updates)


def validate_start_end(
    form: forms.Form,
    data: dict[str, object] | None = None,
    *,
    start_name: str = 'start_date',
    end_name: str = 'end_date',
) -> None:
    """
    Check that the field containing the value of the start field (time, ...) is not bigger (>) than
    the stop.
    """
    data = data or form.cleaned_data
    start, end = data[start_name], data[end_name]
    if start and end and start > end:
        start_label = start_name.replace('_', ' ')
        end_label = end_name.replace('_', ' ')
        form._errors[end_name] = ErrorList([f'The {start_label} cannot be before the {end_label}.'])


__all__ = _all.diff(globals())
