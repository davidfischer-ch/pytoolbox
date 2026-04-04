"""Tests for the voluptuous module."""

# pylint:disable=not-callable,no-value-for-parameter
from __future__ import annotations

import pytest
import voluptuous

from pytoolbox.voluptuous import (
    SHA256,
    Email,
    EmailSet,
    GitCommitHash,
    Password,
    PasswordInvalid,
    Percent,
    Version,
    VersionInvalid,
)

# @voluptuous.message decorated validators must be called once to get
# the actual validator function: Email() returns the validator, then
# Email()('value') validates 'value'.

# Email ------------------------------------------------------------------


def test_email_valid() -> None:
    """Email validator accepts a well-formed address and returns it."""
    assert Email()('user@example.com') == 'user@example.com'


def test_email_invalid() -> None:
    """Email validator raises Invalid for a malformed address."""
    with pytest.raises(voluptuous.Invalid):
        Email()('not-an-email')


def test_email_coerces_to_str() -> None:
    """Email validator coerces non-string input to str before validating."""
    with pytest.raises(voluptuous.Invalid):
        Email()(12345)


# EmailSet ---------------------------------------------------------------


def test_email_set_valid() -> None:
    """EmailSet validator returns a set of valid email strings."""
    result = EmailSet()(['a@b.com', 'c@d.org'])
    assert result == {'a@b.com', 'c@d.org'}


def test_email_set_empty() -> None:
    """EmailSet validator returns an empty set for None or empty input."""
    assert EmailSet()(None) == set()
    assert EmailSet()([]) == set()


def test_email_set_invalid_entry() -> None:
    """EmailSet validator raises Invalid if any address is malformed."""
    with pytest.raises(voluptuous.Invalid):
        EmailSet()(['good@addr.com', 'bad'])


def test_email_set_deduplicates() -> None:
    """EmailSet validator returns unique addresses."""
    result = EmailSet()(['x@y.com', 'x@y.com'])
    assert result == {'x@y.com'}


# GitCommitHash ----------------------------------------------------------


def test_git_commit_hash_valid() -> None:
    """GitCommitHash accepts a 40-char lowercase hex string."""
    h = 'a' * 40
    assert GitCommitHash()(h) == h


def test_git_commit_hash_too_short() -> None:
    """GitCommitHash rejects strings shorter than 40 characters."""
    with pytest.raises(voluptuous.Invalid):
        GitCommitHash()('a' * 39)


def test_git_commit_hash_uppercase() -> None:
    """GitCommitHash rejects uppercase hex characters."""
    with pytest.raises(voluptuous.Invalid):
        GitCommitHash()('A' * 40)


def test_git_commit_hash_non_hex() -> None:
    """GitCommitHash rejects non-hexadecimal characters."""
    with pytest.raises(voluptuous.Invalid):
        GitCommitHash()('g' * 40)


# Password ---------------------------------------------------------------


def test_password_valid() -> None:
    """Password validator accepts strings of sufficient length."""
    validator = Password(length=8)
    # Returns None on success (no return value)
    assert validator('longpassword') is None


def test_password_too_short() -> None:
    """Password validator raises PasswordInvalid for short strings."""
    validator = Password(length=8)
    with pytest.raises(PasswordInvalid):
        validator('short')


def test_password_custom_message() -> None:
    """Password validator uses the custom message when provided."""
    validator = Password(length=8, msg='Too weak')
    with pytest.raises(PasswordInvalid, match='Too weak'):
        validator('abc')


def test_password_default_length() -> None:
    """Password validator defaults to 16 characters minimum."""
    validator = Password()
    with pytest.raises(PasswordInvalid):
        validator('only15charslng!')
    assert validator('sixteen_chars!!!') is None


# Percent ----------------------------------------------------------------


def test_percent_valid() -> None:
    """Percent validator accepts integers between 1 and 100."""
    assert Percent()(1) == 1
    assert Percent()(50) == 50
    assert Percent()(100) == 100


def test_percent_out_of_range() -> None:
    """Percent validator raises Invalid for values outside 1-100."""
    with pytest.raises(voluptuous.Invalid):
        Percent()(0)
    with pytest.raises(voluptuous.Invalid):
        Percent()(101)


# SHA256 -----------------------------------------------------------------


def test_sha256_valid() -> None:
    """SHA256 validator accepts a 64-char lowercase hex string."""
    h = 'abcdef0123456789' * 4
    assert SHA256()(h) == h


def test_sha256_too_short() -> None:
    """SHA256 validator rejects strings shorter than 64 characters."""
    with pytest.raises(voluptuous.Invalid):
        SHA256()('a' * 63)


def test_sha256_uppercase() -> None:
    """SHA256 validator rejects uppercase hex characters."""
    with pytest.raises(voluptuous.Invalid):
        SHA256()('A' * 64)


# Version ----------------------------------------------------------------


def test_version_valid_4_digits() -> None:
    """Version validator with digits=4 accepts 'X.Y.Z.suffix' format."""
    validator = Version(digits=4)
    assert validator('1.2.3.final') == '1.2.3.final'


def test_version_valid_2_digits() -> None:
    """Version validator with digits=2 accepts 'X.suffix' format."""
    validator = Version(digits=2)
    assert validator('1.beta') == '1.beta'


def test_version_invalid() -> None:
    """Version validator raises VersionInvalid for wrong format."""
    validator = Version(digits=4)
    with pytest.raises(VersionInvalid):
        validator('not-a-version')


def test_version_custom_message() -> None:
    """Version validator uses the custom message when provided."""
    validator = Version(digits=3, msg='Bad version')
    with pytest.raises(VersionInvalid, match='Bad version'):
        validator('x')


def test_version_digits_boundary() -> None:
    """Version validator enforces digits between 1 and 4."""
    with pytest.raises(AssertionError):
        Version(digits=0)
    with pytest.raises(AssertionError):
        Version(digits=5)
