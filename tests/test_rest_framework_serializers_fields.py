"""Tests for the rest_framework.serializers.fields module."""

from __future__ import annotations

import pytest
from rest_framework.exceptions import ValidationError

from pytoolbox.rest_framework.serializers.fields import StripCharField

pytestmark = pytest.mark.filterwarnings('ignore:StripCharField is deprecated:DeprecationWarning')


def test_strip_char_field_strips_whitespace() -> None:
    """Leading and trailing whitespace is stripped from input values."""
    field = StripCharField()
    assert field.run_validation('  hello  ') == 'hello'
    assert field.run_validation('no-spaces') == 'no-spaces'


def test_strip_char_field_rejects_blank() -> None:
    """A white-space-only value fails validation with the blank error."""
    with pytest.raises(ValidationError) as error:
        StripCharField().run_validation('   ')
    assert error.value.get_codes() == ['blank']


def test_strip_char_field_is_deprecated() -> None:
    """Creating a StripCharField emits a DeprecationWarning naming its replacement."""
    with pytest.warns(DeprecationWarning, match='CharField'):
        StripCharField()
