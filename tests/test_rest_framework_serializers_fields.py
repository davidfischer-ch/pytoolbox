from __future__ import annotations

import pytest

from pytoolbox.rest_framework.serializers.fields import StripCharField


def test_strip_char_field_strips_whitespace() -> None:
    """Leading and trailing whitespace is stripped from input values."""
    field = StripCharField()
    assert field.to_internal_value('  hello  ') == 'hello'
    assert field.to_internal_value('no-spaces') == 'no-spaces'


def test_strip_char_field_empty_string() -> None:
    """Empty strings pass through without error."""
    field = StripCharField()
    assert field.to_internal_value('') == ''


def test_strip_char_field_has_empty_validator() -> None:
    """EmptyValidator is automatically included in the field's validators."""
    field = StripCharField()
    from pytoolbox.django.core.validators import EmptyValidator
    assert any(isinstance(v, EmptyValidator) for v in field.validators)


def test_strip_char_field_rejects_blank() -> None:
    """Whitespace-only input fails validation via the EmptyValidator."""
    from rest_framework.exceptions import ValidationError as DRFValidationError
    field = StripCharField()
    with pytest.raises(DRFValidationError):
        field.run_validators('   ')
