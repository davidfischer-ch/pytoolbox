from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Final
import os
import re

from . import module

_all = module.All(globals())

ALL_CAP_REGEX: Final[re.Pattern] = re.compile(r'([a-z0-9])([A-Z])')
FIRST_CAP_REGEX: Final[re.Pattern] = re.compile(r'(.)([A-Z][a-z]+)')


def camel_to_dash(string: str) -> str:
    """Convert camelCase to dashed-case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1-\2', string)
    dashed_case_str = ALL_CAP_REGEX.sub(r'\1-\2', sub_string).lower()
    return dashed_case_str.replace('--', '-')


def camel_to_snake(string: str) -> str:
    """Convert camelCase to snake_case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1_\2', string)
    snake_cased_str = ALL_CAP_REGEX.sub(r'\1_\2', sub_string).lower()
    return snake_cased_str.replace('__', '_')


def dash_to_camel(string: str) -> str:
    return _to_camel(string, '-')


def snake_to_camel(string: str) -> str:
    return _to_camel(string, '_')


def _to_camel(string: str, separator: str) -> str:
    components = string.split(separator)
    preffix = suffix = ''
    if components[0] == '':
        components = components[1:]
        preffix = separator
    if components[-1] == '':
        components = components[:-1]
        suffix = separator
    if len(components) > 1:
        camel_case_string = components[0].lower()
        for component in components[1:]:
            if component.isupper() or component.istitle():
                camel_case_string += component
            else:
                camel_case_string += component.title()
    else:
        camel_case_string = components[0]
    return preffix + camel_case_string + suffix


def filterjoin(
    items: Iterable[Any],
    sep: str = ' ',
    keep: Callable[[Any], bool] = bool
) -> str:
    """
    Concatenate `items` with intervening occurrences of `sep`. Gracefully convert items to string
    and filter the items using the `keep` function.
    """
    return sep.join(str(i) for i in items if keep(i))


def to_lines(
    items: Iterable[Any],
    *,
    limit: int = 80,
    start: str = '\t',
    template: str = '{0} '
) -> str:
    """
    Convert items to string using `template`.
    Ensure lines length of maximum `limit`.
    Prefixing every line with `start`.

    **Example usage***

    >>> some_culture = (  # Credits: https://en.wikipedia.org/wiki/Punched_card
    ...     "A legacy of the 80 column punched card format is that a display of 80 characters per"
    ...     " row was a common choice in the design of character-based terminals. As of November"
    ...     " 2011 some character interface defaults, such as the command prompt window's width"
    ...     " in Microsoft Windows, remain set at 80 columns and some file formats, such as FITS,"
    ...     " still use 80-character card images.")

    Using default options:

    >>> print(to_lines(some_culture.split(' ')))
        A legacy of the 80 column punched card format is that a display of 80
        characters per row was a common choice in the design of character-based
        terminals. As of November 2011 some character interface defaults, such as the
        command prompt window's width in Microsoft Windows, remain set at 80 columns
        and some file formats, such as FITS, still use 80-character card images.

    Customizing output:

    >>> print(to_lines(some_culture.split(' '), limit=42, start='> '))
    > A legacy of the 80 column punched card
    > format is that a display of 80
    > characters per row was a common choice
    > in the design of character-based
    > terminals. As of November 2011 some
    > character interface defaults, such as
    > the command prompt window's width in
    > Microsoft Windows, remain set at 80
    > columns and some file formats, such as
    > FITS, still use 80-character card
    > images.

    Displaying objects representation:

    >>> class Item(object):
    ...     def __init__(self, value):
    ...         self.value = value
    ...
    ...     def __repr__(self):
    ...         return f'<Item value={self.value}>'
    ...
    >>> print(to_lines((Item(i) for i in range(22)), limit=60, template='{0!r} '))
        <Item value=0> <Item value=1> <Item value=2>
        <Item value=3> <Item value=4> <Item value=5>
        <Item value=6> <Item value=7> <Item value=8>
        <Item value=9> <Item value=10> <Item value=11>
        <Item value=12> <Item value=13> <Item value=14>
        <Item value=15> <Item value=16> <Item value=17>
        <Item value=18> <Item value=19> <Item value=20>
        <Item value=21>
    """
    lines = [start]
    for item in items:
        item_str = template.format(item)
        if len(lines[-1]) + len(item_str) > limit:
            lines.append(start)
        lines[-1] += item_str
    return os.linesep.join(lines)


__all__ = _all.diff(globals())
