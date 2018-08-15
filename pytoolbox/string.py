# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, re

from . import module
from .encoding import text_type

_all = module.All(globals())

ALL_CAP_REGEX = re.compile(r'([a-z0-9])([A-Z])')
FIRST_CAP_REGEX = re.compile(r'(.)([A-Z][a-z]+)')


def camel_to_dash(string):
    """Convert camelCase to dashed-case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1-\2', string)
    dashed_case_str = ALL_CAP_REGEX.sub(r'\1-\2', sub_string).lower()
    return dashed_case_str.replace('--', '-')


def camel_to_snake(string):
    """Convert camelCase to snake_case."""
    sub_string = FIRST_CAP_REGEX.sub(r'\1_\2', string)
    snake_cased_str = ALL_CAP_REGEX.sub(r'\1_\2', sub_string).lower()
    return snake_cased_str.replace('__', '_')


def dash_to_camel(string):
    return _to_camel(string, '-')


def snake_to_camel(string):
    return _to_camel(string, '_')


def _to_camel(string, separator):
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
        for x in components[1:]:
            if x.isupper() or x.istitle():
                camel_case_string += x
            else:
                camel_case_string += x.title()
    else:
        camel_case_string = components[0]
    return preffix + camel_case_string + suffix


def filterjoin(items, sep=' ', keep=lambda o: o):
    """
    Concatenate `items` with intervening occurrences of `sep`. Gracefully convert items to string
    and filter the items using the `keep` function.
    """
    return sep.join(text_type(i) for i in items if keep(i))


def to_lines(items, limit=80, start='\t', line='{0} '):
    lines = [start]
    for item in items:
        item_str = line.format(item)
        if len(lines[-1]) + len(item_str) > limit:
            lines.append(start)
        lines[-1] += item_str
    return os.linesep.join(lines)


__all__ = _all.diff(globals())
