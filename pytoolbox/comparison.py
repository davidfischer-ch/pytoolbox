from typing import Iterator, Optional
import difflib, operator as op, os
from packaging.version import parse as parse_version, LegacyVersion, Version

import termcolor

from .types import get_slots

__all__ = [
    'SlotsEqualityMixin',
    'unified_diff',
    'VERSION_OPERATIONS',
    'LegacyVersion',
    'Version',
    'compare_versions',
    'parse_version',
    'satisfy_version_constraints'
]


class SlotsEqualityMixin(object):
    """
    Implement the comparison operators based on the slots.
    Both the name of the slots retrieved with :func:`pytoolbox.types.get_slots`
    and theirs values are tested for equality.
    """

    def __eq__(self, other):
        return get_slots(self) == get_slots(other) and \
            all(getattr(self, a) == getattr(other, a) for a in get_slots(self))

    def __ne__(self, other):
        return not self.__eq__(other)


# Content ------------------------------------------------------------------------------------------

def unified_diff(before: str, after: str, *, colorize: bool = True, **kwargs) -> str:
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

def _eqn(a, b) -> Optional[bool]:  # pylint:disable=invalid-name
    return True if a == b else None


def _nen(a, b) -> Optional[bool]:  # pylint:disable=invalid-name
    return False if a == b else None


VERSION_OPERATIONS = {
    Version: {'<': op.lt, '<=': op.le, '==': op.eq, '!=': op.ne, '>=': op.ge, '>': op.gt},
    LegacyVersion: {'<': _nen, '<=': _eqn, '==': op.eq, '!=': op.ne, '>=': _eqn, '>': _nen}
}


def compare_versions(
    a: str,  # pylint:disable=invalid-name
    b: str,  # pylint:disable=invalid-name
    operator: str
) -> Optional[bool]:
    version_a = parse_version(a)
    version_b = parse_version(b)
    if type(version_a) is type(version_b):
        operation = VERSION_OPERATIONS[type(version_a)][operator]
        return operation(version_a, version_b) if operation else None
    return None  # Will not try to compare Version to LegacyVersion


def satisfy_version_constraints(
    version: Optional[str],
    constraints: tuple[str, ...], *,
    default='<undefined>',
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
