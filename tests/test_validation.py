"""Tests for the validation module."""

from __future__ import annotations

import pytest

from pytoolbox.validation import valid_email, valid_filename, valid_secret, validate_list


def test_validate_list() -> None:
    """validate_list() validates each element against a regex pattern."""
    regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
    validate_list([10, "call(['my_var', recursive=False])"], regexes)


def test_validate_list_fail_size() -> None:
    """validate_list() raises IndexError when list sizes don't match."""
    with pytest.raises(IndexError):
        validate_list([1, 2], [1, 2, 3])


def test_validate_list_fail_value() -> None:
    """validate_list() raises ValueError when element doesn't match regex."""
    with pytest.raises(ValueError):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call(['my_var', recursive='error'])"], regexes)


def test_valid_filename_non_string() -> None:
    """valid_filename returns False for non-string input."""
    assert valid_filename(None) is False


def test_valid_filename_refuses_a_path() -> None:
    """The whole string must be one file name: a path or a NUL byte is refused."""
    assert valid_filename('archive.tar.gz') is True
    assert valid_filename('a.b/../../etc/passwd') is False
    assert valid_filename('a.b/c') is False
    assert valid_filename('a.b\\c') is False
    assert valid_filename('x.y\0') is False


def test_valid_email_non_string() -> None:
    """valid_email returns False for non-string input."""
    assert valid_email(None) is False


def test_valid_email_refuses_a_valid_prefix_followed_by_more() -> None:
    """The whole string must be one address: a header injection or a second address is refused."""
    assert valid_email('a@b.ch\nBcc: v@x.org') is False
    assert valid_email('a@b.c d') is False
    assert valid_email('a@b.c@evil.org') is False


def test_valid_secret_non_string() -> None:
    """valid_secret returns False for non-string, non-None input."""
    assert valid_secret(42, none_allowed=False) is False
