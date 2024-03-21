from __future__ import annotations

from collections.abc import Iterator
from typing import TypeAlias
import difflib
import operator as op
import os

from packaging.version import (  # pylint:disable=ungrouped-imports
    parse as _parse_version,
    InvalidVersion,
    Version
)

import termcolor

from .types import get_slots

__all__ = [
    'SlotsEqualityMixin',
    'unified_diff',
    'VERSION_OPERATIONS',
    'Version',
    'compare_versions',
    'satisfy_version_constraints',
    'try_parse_version'
]


class SlotsEqualityMixin(object):
    """
    Implement the comparison operators based on the slots.
    Both the name of the slots retrieved with :func:`pytoolbox.types.get_slots`
    and theirs values are tested for equality.
    """

    def __eq__(self, other) -> bool:
        return get_slots(self) == get_slots(other) and \
            all(getattr(self, a) == getattr(other, a) for a in get_slots(self))

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


# Content ------------------------------------------------------------------------------------------

def unified_diff(before: str, after: str, *, colorize: bool = True, **kwargs) -> str:
    """
    Colorization is not guaranteed (your environment may disable it).
    Use `pytoolbox.console.toggle_colors` appropriately to ensure it.
    """
    diff = difflib.unified_diff(before.splitlines(), after.splitlines(), **kwargs)
    return os.linesep.join(_colorize(diff) if colorize else diff)


def _colorize(diff: Iterator[str]) -> Iterator[str]:
    for line in diff:
        if line.startswith('+'):
            yield termcolor.colored(line, 'green')
        elif line.startswith('-'):
            yield termcolor.colored(line, 'red')
        elif line.startswith('^'):
            yield termcolor.colored(line, 'blue')
        else:
            yield line


# Versions -----------------------------------------------------------------------------------------

def _eqn(a, b) -> bool | None:  # pylint:disable=invalid-name
    return True if a == b else None


def _nen(a, b) -> bool | None:  # pylint:disable=invalid-name
    return False if a == b else None


VERSION_OPERATIONS: dict = {  # pylint:disable=consider-using-namedtuple-or-dataclass
    Version: {'<': op.lt, '<=': op.le, '==': op.eq, '!=': op.ne, '>=': op.ge, '>': op.gt},
    str: {'<': _nen, '<=': _eqn, '==': op.eq, '!=': op.ne, '>=': _eqn, '>': _nen}
}


try:
    from packaging.version import LegacyVersion  # type: ignore[attr-defined]
    VERSION_OPERATIONS[LegacyVersion] = VERSION_OPERATIONS[str]
    ParseVersionTypes: TypeAlias = str | Version | LegacyVersion
except ImportError:
    ParseVersionTypes: TypeAlias = str | Version  # type: ignore[misc, no-redef]


def compare_versions(
    a: str,  # pylint:disable=invalid-name
    b: str,  # pylint:disable=invalid-name
    operator: str
) -> bool | None:
    version_a = try_parse_version(a)
    version_b = try_parse_version(b)
    if type(version_a) is type(version_b):
        operation = VERSION_OPERATIONS[type(version_a)][operator]
        return operation(version_a, version_b) if operation else None
    return None  # Will not try to compare Version to LegacyVersion


def satisfy_version_constraints(
    version: str | None,
    constraints: tuple[str, ...], *,
    default: str = '<undefined>',
) -> bool:
    """
    Ensure given version fulfill the constraints (if any).

    Constraints are given in the form '<operator> <version>', Exemple:

    >>> satisfy_version_constraints('v1.5.2', ['>= v1.5', '< v2'])
    True
    >>> satisfy_version_constraints('v0.7', ['>= v1.5', '< v2'])
    False
    >>> satisfy_version_constraints(None, ['>= v1.5', '< v2'])
    False
    >>> satisfy_version_constraints('main', ['!= main'])
    False
    >>> satisfy_version_constraints(None, ['== <undefined>'])
    True
    >>> satisfy_version_constraints(None, ['!= master'], default='master')
    False
    """
    return all(compare_versions(version or default, *c.split(' ')[::-1]) for c in constraints or [])


def try_parse_version(version: str) -> ParseVersionTypes:
    try:
        return _parse_version(version)
    except InvalidVersion:
        return version
