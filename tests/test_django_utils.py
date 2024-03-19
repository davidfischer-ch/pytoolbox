# pylint:disable=too-few-public-methods
from __future__ import annotations

import pytest


class File(object):
    pass


class Media(object):
    pass


class MediaForm(object):
    class Meta:
        model = Media


@pytest.mark.skip(reason='Django modules testing disabled')
def test_fields_to_values_lookup_dict() -> None:
    from pytoolbox.django.utils import collections
    numbers = collections.FieldsToValuesLookupDict(
        'numbers', {'MediaForm.name': 1, 'Media.url': 2, 'url': 3})
    assert numbers[(File, 'url')] == 3
    assert numbers[(Media, 'url')] == 2
    assert numbers[(MediaForm, 'url')] == 2
    assert numbers[(MediaForm, 'name')] == 1
