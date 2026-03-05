from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured, ValidationError
import pytest

from pytoolbox.django.core import validators


def test_keys_validator_required_keys() -> None:
    validator = validators.KeysValidator(required_keys=['name', 'age'])
    validator({'name': 'Alice', 'age': 30})
    with pytest.raises(ValidationError) as exc_info:
        validator({'name': 'Alice'})
    assert exc_info.value.code == 'missing_keys'


def test_keys_validator_strict() -> None:
    validator = validators.KeysValidator(
        required_keys=['name'],
        optional_keys=['age'],
        strict=True)
    validator({'name': 'Alice'})
    validator({'name': 'Alice', 'age': 30})
    with pytest.raises(ValidationError) as exc_info:
        validator({'name': 'Alice', 'unknown': True})
    assert exc_info.value.code == 'extra_keys'


def test_keys_validator_requires_at_least_one_key_set() -> None:
    with pytest.raises(ImproperlyConfigured):
        validators.KeysValidator()


def test_keys_validator_equality() -> None:
    a = validators.KeysValidator(required_keys=['x'])
    b = validators.KeysValidator(required_keys=['x'])
    c = validators.KeysValidator(required_keys=['y'])
    assert a == b
    assert a != c


def test_empty_validator() -> None:
    validator = validators.EmptyValidator()
    validator('hello')
    with pytest.raises(ValidationError):
        validator('   ')


def test_md5_checksum_validator() -> None:
    validator = validators.MD5ChecksumValidator()
    validator('d41d8cd98f00b204e9800998ecf8427e')
    with pytest.raises(ValidationError):
        validator('not-a-checksum')
