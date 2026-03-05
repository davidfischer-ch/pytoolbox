# pylint:disable=no-member
from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from pytoolbox.django.forms import utils


def test_update_widget_attributes_add_remove_toggle() -> None:
    widget = MagicMock()
    widget.attrs = {'class': 'mondiale'}
    utils.update_widget_attributes(widget, {'class': '+pigeon +voyage -mondiale ^voyageur'})
    classes = set(widget.attrs['class'].split())
    assert 'pigeon' in classes
    assert 'voyage' in classes
    assert 'voyageur' in classes
    assert 'mondiale' not in classes


def test_update_widget_attributes_non_class() -> None:
    widget = MagicMock()
    widget.attrs = {}
    utils.update_widget_attributes(widget, {'cols': 100, 'rows': 20})
    assert widget.attrs['cols'] == 100
    assert widget.attrs['rows'] == 20


def test_update_widget_attributes_invalid_operation() -> None:
    widget = MagicMock()
    widget.attrs = {}
    with pytest.raises(ValueError, match='valid string'):
        utils.update_widget_attributes(widget, {'class': 'noop'})


def test_conditional_required() -> None:
    form = MagicMock()
    form._errors = {}
    form.cleaned_data = {'name': '', 'age': 25}
    utils.conditional_required(form, {'name': True, 'age': False})
    assert 'name' in form._errors
    assert 'age' not in form._errors


def test_conditional_required_cleanup() -> None:
    form = MagicMock()
    form._errors = {}
    data = {'optional': 'value'}
    utils.conditional_required(form, {'optional': False}, data=data, cleanup=True)
    assert data['optional'] is None


def test_set_disabled() -> None:
    form = MagicMock()
    form.fields = {'name': MagicMock()}
    form.fields['name'].widget.attrs = {}
    utils.set_disabled(form, 'name', value=True)
    assert form.fields['name'].widget.attrs['disabled'] is True
    utils.set_disabled(form, 'name')
    assert 'disabled' not in form.fields['name'].widget.attrs


def test_validate_start_end() -> None:
    form = MagicMock()
    form._errors = {}
    form.cleaned_data = {
        'start_date': datetime.date(2025, 3, 10),
        'end_date': datetime.date(2025, 3, 1)
    }
    utils.validate_start_end(form)
    assert 'end_date' in form._errors
