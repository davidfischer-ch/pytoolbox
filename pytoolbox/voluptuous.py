"""
Module containing extensions to validate data with
`voluptuous <https://github.com/alecthomas/voluptuous>`_.
"""
from __future__ import annotations


from collections.abc import Callable
import functools
import re

import voluptuous

from . import module, validation

_all = module.All(globals())


# Errors

class PasswordInvalid(voluptuous.Invalid):
    """Incorrect password."""


class VersionInvalid(voluptuous.Invalid):
    """Incorrect version number."""


# Validators

@voluptuous.message('Incorrect e-mail address')
def Email(value: str) -> str:  # noqa: N802
    """Validate and return an e-mail address string."""
    value = str(value)
    if not validation.valid_email(value):
        raise ValueError
    return value


@voluptuous.message('Incorrect list of e-mail addresses')
def EmailSet(values: list[str] | None) -> set[str]:  # noqa: N802
    """Validate and return a set of e-mail address strings."""
    emails = set()
    for value in values or []:
        email = str(value)
        if not validation.valid_email(email):
            raise ValueError
        emails.add(email)
    return emails


@voluptuous.message('Incorrect git commit hash')
def GitCommitHash(value: str) -> str:  # noqa: N802
    """Validate and return a 40-character hexadecimal Git commit hash."""
    if re.match(r'^[0-9a-f]{40}$', value):
        return value
    raise ValueError


def Password(length: int = 16, msg: str | None = None) -> Callable:  # noqa: N802
    """Return a validator requiring a password of at least ``length`` characters."""

    @functools.wraps(Password)
    def f(value: str) -> None:
        value = str(value)
        if len(value) < length:
            raise PasswordInvalid(msg or 'Incorrect password')
    return f


@voluptuous.message('Incorrect percentage')
def Percent(value: int) -> int:  # noqa: N802
    """Validate that a value is a percentage between 1 and 100."""
    return voluptuous.Range(min=1, max=100)(value)


@voluptuous.message('Incorrect SHA-256 checksum')
def SHA256(value: str) -> str:  # noqa: N802
    """Validate and return a 64-character hexadecimal SHA-256 checksum."""
    if re.match(r'^[0-9a-f]{64}$', value):
        return value
    raise ValueError


def Version(digits: int = 4, msg: str | None = None) -> Callable:  # noqa: N802
    """Return a validator for version strings with the given number of ``digits``."""
    assert 1 <= digits <= 4
    pattern = r'^[0-9]+(\.[0-9]+){%d}\.[a-z0-9]+$'

    @functools.wraps(Version)
    def f(value: str) -> str:
        if re.match(pattern % (digits - 2), value):  # pylint:disable=consider-using-f-string
            return value
        raise VersionInvalid(msg or 'Incorrect version number')
    return f


__all__ = _all.diff(globals())
