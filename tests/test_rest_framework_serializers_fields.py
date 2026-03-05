from __future__ import annotations

import pytest

from pytoolbox.rest_framework.serializers.fields import StripCharField


def test_strip_char_field_strips_whitespace() -> None:
    field = StripCharField()
    assert field.to_internal_value('  hello  ') == 'hello'
    assert field.to_internal_value('no-spaces') == 'no-spaces'


def test_strip_char_field_empty_string() -> None:
    field = StripCharField()
    assert field.to_internal_value('') == ''


def test_strip_char_field_has_empty_validator() -> None:
    field = StripCharField()
    from pytoolbox.django.core.validators import EmptyValidator
    assert any(isinstance(v, EmptyValidator) for v in field.validators)


def test_strip_char_field_rejects_blank() -> None:
    from rest_framework.exceptions import ValidationError as DRFValidationError
    field = StripCharField()
    with pytest.raises(DRFValidationError):
        field.run_validators('   ')
