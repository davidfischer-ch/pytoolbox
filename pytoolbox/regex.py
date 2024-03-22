from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Final, Literal, overload
import fnmatch
import re

from .itertools import chain

__all__ = [
    'TIME_REGEX_PARTS',
    'UUID_REGEX',
    'embed_in_regex',
    'findall_partial',
    'from_path_patterns'
]

TIME_REGEX_PARTS: Final[list[str]] = [
    '[0-2]', '[0-9]', ':',
    '[0-5]', '[0-9]', ':',
    '[0-5]', '[0-9]'
]

UUID_REGEX: Final[str] = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


@overload
def embed_in_regex(
    string: str,
    regex_parts: list[str],
    index: int,
    *,
    as_string: Literal[True] = True
) -> tuple[int, str]:
    ...


@overload
def embed_in_regex(
    string: str,
    regex_parts: list[str],
    index: int,
    *,
    as_string: Literal[False]
) -> tuple[int, list[str]]:
    ...


def embed_in_regex(string, regex_parts, index, as_string=True):
    """
    **Example usage**

    >>> embed_in_regex('L', ['[a-z]', '[a-z]'], 0)
    (0, 'L[a-z]')
    >>> embed_in_regex('L', ['[a-z]', '[a-z]'], 1)
    (1, '[a-z]L')
    >>> embed_in_regex('L', ['[a-z]', '[a-z]'], 1, as_string=False)
    (1, ['[a-z]', 'L'])
    """
    regex = regex_parts[:]
    regex[index:index + len(string)] = string
    return index, ''.join(regex) if as_string else regex


def findall_partial(string: str, regex_parts: list[str]) -> Iterator[tuple[str, list[str], int]]:
    """
    **Example usage**

    >>> [i for s, r, i in findall_partial(':', TIME_REGEX_PARTS)]
    [2, 5]
    >>> [embed_in_regex(s, r, i) for s, r, i in findall_partial('12:15:2', TIME_REGEX_PARTS)]
    [(0, '12:15:2[0-9]')]
    >>> [embed_in_regex(s, r, i) for s, r, i in findall_partial('18:2', TIME_REGEX_PARTS)]
    [(0, '18:2[0-9]:[0-5][0-9]'), (3, '[0-2][0-9]:18:2[0-9]')]
    >>> [embed_in_regex(s, r, i) for s, r, i in findall_partial('59:1', TIME_REGEX_PARTS)]
    [(3, '[0-2][0-9]:59:1[0-9]')]
    """
    for index in range(0, len(regex_parts) - len(string) + 1):
        regex = regex_parts[index:index + len(string)]
        if re.search(''.join(regex), string):
            yield string, regex_parts, index


def from_path_patterns(
    patterns: re.Pattern | str | list[re.Pattern] | list[str] | list[re.Pattern | str],
    *,
    regex: bool = False
) -> list[re.Pattern]:
    """
    Return patterns compiled to regular expressions, if necessary.

    If `regex` is set to False, then any string pattern will be converted from the unix-style
    wildcard to the regular expression equivalent using :func:`fnatmch.translate`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns('*.txt')],
    ...     ['(?s:.*\\\\.txt)\\\\Z'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns(['text', 'something*'], regex=True)],
    ...     ['text', 'something*'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns([re.compile('a?c'), 'fo?'])],
    ...     ['a?c', '(?s:fo.)\\\\Z'])
    >>> asserts.list_equal(
    ...     [r.pattern for r in from_path_patterns([re.compile('a?c'), 'foo?'], regex=True)],
    ...     ['a?c', 'foo?'])
    """
    return [
        p if isinstance(p, re.Pattern) else re.compile(p if regex else fnmatch.translate(p))
        for p in chain(patterns)
    ]


class Match(object):
    """
    Assert that a given string meets some expectations.

    If this is not a string, then for sure its not equal.

    Credits: https://kalnytskyi.com/howto/assert-str-matches-regex-in-pytest/

    **Example usage**

    >>> assert 'foobar' == Match(r'foo')
    >>> assert 'foobar' != Match(r'foo$')
    >>> assert 'baz' != Match(r'foo')
    >>> assert None != Match(r'foo')
    >>> assert b'foo' != Match(r'foo.*')
    >>> repr(Match(r'foo.+'))
    'foo.+'
    """
    def __init__(self, pattern: str, flags: int = 0) -> None:
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual: Any) -> bool:
        try:
            return self._regex.match(actual) is not None
        except TypeError:
            return False

    def __repr__(self) -> str:
        return self._regex.pattern
