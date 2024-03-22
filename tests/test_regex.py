from __future__ import annotations

import re

from pytest import mark, raises
from pytoolbox import exceptions, regex


@mark.parametrize('mapping, expected', [
    (
        (
            ('money', 'EUR'),
            ('amount', '110')
        ),
        'Our price 110 EUR'
    ),
    (
        (
            ('money', 'XMR'),
            ('amount', '35')
        ),
        'Our price 35 XMR'
    ),
    (
        (
            ('amount', '35'),
            ('money', 'XMR')
        ),
        # Known issue here (mutating string not in reverse order)
        'Our price 35 CXMR'
    ),
    (
        (
            ('money', 'EUR'),
            ('amount', None)
        ),
        'Our price 100 EUR'
    ),
    (
        (
            ('amount', '1000'),
        ),
        'Our price 1000 CHF'
    )
])
def test_group_replace(mapping, expected: str) -> None:
    pattern = re.compile(r'(?P<amount>\d+) (?P<money>[A-Z]{3})')
    text = 'Our price 100 CHF'
    match = pattern.search(text)
    assert regex.group_replace(text, match, mapping=mapping) == expected


def test_group_replace_optional_group() -> None:
    pattern = re.compile(r'(?P<amount>\d+)? (?P<money>[A-Z]{3})')
    text = 'Our price: CHF'
    match = pattern.search(text)
    with raises(exceptions.RegexMatchGroupNotFoundError, match='Group "amount" not found'):
        regex.group_replace(text, match, mapping=[('amount', 'FOO')])


def test_group_replace_wrong_group() -> None:
    pattern = re.compile(r'(?P<amount>\d+) (?P<money>[A-Z]{3})')
    text = 'Our price 100 CHF'
    match = pattern.search(text)
    with raises(exceptions.RegexMatchGroupNotFoundError, match='Group "wrong" not found'):
        regex.group_replace(text, match, mapping=[('wrong', 'foo')])


def test_match_equality():
    # pylint:disable=misplaced-comparison-constant
    assert regex.Match(r'some-s[a-z]+') == 'some-string'
    assert 'some-string' == regex.Match(r'some-s[a-z]+')
    assert 'some-string' != regex.Match(r'other-s[a-z]+')


def test_match_repr():
    assert repr(regex.Match(r'\s+')) == '\\s+'
