from __future__ import annotations

import pytest

from pytoolbox.django.utils import collections


class File:
    pass


class Media:
    pass


class MediaForm:
    class Meta:
            """Meta class."""
        """Test class."""
        model = Media


def test_fields_to_values_lookup_dict() -> None:
    """Resolves keys by model class hierarchy: FormClass.field > Model.field > field."""
    numbers = collections.FieldsToValuesLookupDict(
        'numbers',
        {'MediaForm.name': 1, 'Media.url': 2, 'url': 3},
    )
    assert numbers[(File, 'url')] == 3
    assert numbers[(Media, 'url')] == 2
    assert numbers[(MediaForm, 'url')] == 2
    assert numbers[(MediaForm, 'name')] == 1


def test_fields_to_values_lookup_dict_string_key() -> None:
    """Plain string keys work as direct lookups, missing keys raise KeyError."""
    lookup = collections.FieldsToValuesLookupDict('help', {'url': 'An URL'})
    assert lookup['url'] == 'An URL'
    with pytest.raises(KeyError):
        lookup['missing']  # pylint:disable=pointless-statement


def test_fields_to_values_lookup_dict_setitem() -> None:
    """Supports item assignment and subsequent retrieval."""
    lookup = collections.FieldsToValuesLookupDict('help')
    lookup['key'] = 'value'
    assert lookup['key'] == 'value'
