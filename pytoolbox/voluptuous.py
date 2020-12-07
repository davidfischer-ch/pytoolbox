"""
Module containing extensions to validate data with
`voluptuous <https://github.com/alecthomas/voluptuous>`_.
"""

import functools, re

import voluptuous

from . import module, validation

_all = module.All(globals())


# Errors

class PasswordInvalid(voluptuous.Invalid):
    """Incorrect password"""


class VersionInvalid(voluptuous.Invalid):
    """Incorrect version number"""


# Validators

@voluptuous.message('Incorrect e-mail address')
def Email(value):  # pylint:disable=invalid-name
    value = str(value)
    if not validation.valid_email(value):
        raise ValueError
    return value


@voluptuous.message('Incorrect list of e-mail addresses')
def EmailSet(values):  # pylint:disable=invalid-name
    emails = set()
    for value in values or []:
        email = str(value)
        if not validation.valid_email(email):
            raise ValueError
        emails.add(email)
    return emails


@voluptuous.message('Incorrect git commit hash')
def GitCommitHash(value):  # pylint:disable=invalid-name
    if re.match(r'^[0-9a-f]{40}$', value):
        return value
    raise ValueError


def Password(length=16, msg=None):  # pylint:disable=invalid-name

    @functools.wraps(Password)
    def f(value):
        value = str(value)
        if len(value) < length:
            raise PasswordInvalid(msg or 'Incorrect password')
    return f


@voluptuous.message('Incorrect percentage')
def Percent(value):  # pylint:disable=invalid-name
    return voluptuous.Range(min=1, max=100)(value)


@voluptuous.message('Incorrect SHA-256 checksum')
def SHA256(value):  # pylint:disable=invalid-name
    if re.match(r'^[0-9a-f]{64}$', value):
        return value
    raise ValueError


def Version(digits=4, msg=None):  # pylint:disable=invalid-name
    assert 1 <= digits <= 4

    @functools.wraps(Version)
    def f(value):
        if re.match(r'^[0-9]+(\.[0-9]+){%d}\.[a-z0-9]+$' % (digits - 2), value):
            return value
        raise VersionInvalid(msg or 'Incorrect version number')
    return f


__all__ = _all.diff(globals())
