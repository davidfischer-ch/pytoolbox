from __future__ import annotations

from pytoolbox import regex


def test_match_equality():
    # pylint:disable=misplaced-comparison-constant
    assert regex.Match(r'some-s[a-z]+') == 'some-string'
    assert 'some-string' == regex.Match(r'some-s[a-z]+')
    assert 'some-string' != regex.Match(r'other-s[a-z]+')


def test_match_repr():
    assert repr(regex.Match(r'\s+')) == '\\s+'
