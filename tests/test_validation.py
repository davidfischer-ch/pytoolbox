import pytest
from pytoolbox.validation import validate_list


def test_validate_list():
    regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
    validate_list([10, "call(['my_var', recursive=False])"], regexes)


def test_validate_list_fail_size():
    with pytest.raises(IndexError):
        validate_list([1, 2], [1, 2, 3])


def test_validate_list_fail_value():
    with pytest.raises(ValueError):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call(['my_var', recursive='error'])"], regexes)
