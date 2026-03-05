from __future__ import annotations

import pytest

from pytoolbox.django.utils import collections


class File:
    pass


class Media:
    pass


class MediaForm:
    class Meta:
        model = Media


def test_fields_to_values_lookup_dict() -> None:
    numbers = collections.FieldsToValuesLookupDict(
        'numbers',
        {'MediaForm.name': 1, 'Media.url': 2, 'url': 3})
    assert numbers[(File, 'url')] == 3
    assert numbers[(Media, 'url')] == 2
    assert numbers[(MediaForm, 'url')] == 2
    assert numbers[(MediaForm, 'name')] == 1


def test_fields_to_values_lookup_dict_string_key() -> None:
    lookup = collections.FieldsToValuesLookupDict('help', {'url': 'An URL'})
    assert lookup['url'] == 'An URL'
    with pytest.raises(KeyError):
        lookup['missing']  # pylint:disable=pointless-statement


def test_fields_to_values_lookup_dict_setitem() -> None:
    lookup = collections.FieldsToValuesLookupDict('help')
    lookup['key'] = 'value'
    assert lookup['key'] == 'value'
