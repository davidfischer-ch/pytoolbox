"""Tests for the django.core.exceptions module."""

from __future__ import annotations

from django.core.exceptions import ValidationError

from pytoolbox.django.core import exceptions


def test_get_message() -> None:
    """Interpolates params into the ValidationError message template."""
    error = ValidationError('Field %(field)s is bad', params={'field': 'name'})
    assert exceptions.get_message(error) == 'Field name is bad'
    simple = ValidationError('plain error')
    assert exceptions.get_message(simple) == 'plain error'


def test_has_code() -> None:
    """Detects error codes in simple, dict-wrapped, and list-wrapped ValidationErrors."""
    assert not exceptions.has_code(ValidationError('yo'), 'bad')
    assert exceptions.has_code(ValidationError('yo', code='bad'), 'bad')
    assert exceptions.has_code(
        ValidationError({'__all__': ValidationError('yo', code='bad')}),
        'bad',
    )
    assert exceptions.has_code(
        ValidationError([ValidationError('yo', code='bad')]),
        'bad',
    )


def test_iter_validation_errors() -> None:
    """Yields (field, error) pairs from simple, dict-keyed, and list ValidationErrors."""
    bad = ValidationError('yo', code='bad')
    assert list(exceptions.iter_validation_errors(bad)) == [(None, bad)]
    boy = ValidationError('yo', code='boy')
    result = list(exceptions.iter_validation_errors(ValidationError({'__all__': boy})))
    assert result == [('__all__', boy)]
    result = list(exceptions.iter_validation_errors(ValidationError([bad, boy])))
    assert result == [(None, bad), (None, boy)]
