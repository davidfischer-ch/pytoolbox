from __future__ import annotations

import pytest
from pytoolbox.private import _parse_kwargs_string


def test_parse_kwargs_string() -> None:
    assert _parse_kwargs_string('year=1950 ;  style=jazz', year=int, style=str) == {
        'year': 1950,
        'style': 'jazz'
    }
    assert _parse_kwargs_string(' like_it=True ', like_it=lambda x: x == 'True') == {
        'like_it': True
    }


def test_parse_kwargs_string_key_error() -> None:
    with pytest.raises(KeyError):
        _parse_kwargs_string(' pi=3.1416; ru=2', pi=float)


def test_parse_kwargs_string_value_error() -> None:
    with pytest.raises(ValueError):
        _parse_kwargs_string(' a_number=yeah', a_number=int)
