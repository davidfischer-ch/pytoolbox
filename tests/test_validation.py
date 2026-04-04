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


def test_valid_email_non_string() -> None:
    """valid_email returns False for non-string input."""
    assert valid_email(None) is False


def test_valid_secret_non_string() -> None:
    """valid_secret returns False for non-string, non-None input."""
    assert valid_secret(42, none_allowed=False) is False
