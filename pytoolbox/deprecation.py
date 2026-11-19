"""
Deprecation helpers: deprecated functions, and renamed methods kept reachable under their old names.
"""

from __future__ import annotations

import functools
import inspect
import types
import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

__all__ = ['alias_renamed_methods', 'deprecated']


def alias_renamed_methods(cls: type, renames: Mapping[str, str]) -> None:
    """
    Alias each old name of *renames* and its new name to one method on every class of *cls*'s MRO.

    Call it from the base's :meth:`object.__init_subclass__`. A class defining only the old name
    gets the new one as an alias, and a :class:`DeprecationWarning` located at that method's
    definition. A class defining only the new name gets the old one as an alias. A class defining
    both keeps both as written. A caller of either name, and a :func:`super` chain through either,
    then reaches the same methods. The base gains the old name with its first subclass.

    **Example usage**

    >>> import warnings
    >>> class Base:
    ...     def __init_subclass__(cls, **kwargs):
    ...         super().__init_subclass__(**kwargs)
    ...         alias_renamed_methods(cls, {'get_label': 'label'})
    ...
    ...     def label(self):
    ...         return 'base'
    >>> with warnings.catch_warnings(record=True) as caught:
    ...     warnings.simplefilter('always')
    ...
    ...     class Legacy(Base):
    ...         def get_label(self):
    ...             return 'legacy'
    >>> [str(warning.message) for warning in caught]
    ['Legacy.get_label is deprecated; override label instead.']
    >>> Legacy().label(), Legacy().get_label()
    ('legacy', 'legacy')
    """
    for klass in cls.__mro__:
        members = vars(klass)
        for old, new in renames.items():
            if old in members and new not in members:
                message = f'{klass.__qualname__}.{old} is deprecated; override {new} instead.'
                _warn_renamed(members[old], message)
                setattr(klass, new, members[old])
            elif new in members and old not in members:
                setattr(klass, old, members[new])


def deprecated(guidelines: str = '') -> Callable:
    """Return a decorator that marks a function as deprecated."""

    def _deprecated(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Emit a :class:`DeprecationWarning` located at the function's definition on every call.

        Credits: https://wiki.python.org/moin/PythonDecoratorLibrary.
        """
        guidelines_suffix = f': {guidelines}' if guidelines else ''
        message = f'{func.__qualname__} is deprecated{guidelines_suffix}.'

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _warn_at_definition(func, message)
            return func(*args, **kwargs)

        return wrapper

    return _deprecated


def _warn_renamed(member: Any, message: str) -> None:
    """
    Emit *message* as a :class:`DeprecationWarning` located at the definition of *member*.

    Locate a :class:`classmethod` by its ``__func__``, a :class:`property` by its getter, a
    :class:`functools.cached_property` by its function, and a wrapper by the function it wraps.
    """
    for attribute in ('__func__', 'fget', 'func'):
        member = getattr(member, attribute, member)
    function = inspect.unwrap(member)
    if not isinstance(function, types.FunctionType):
        # A member without code: the warning names the base's call to alias_renamed_methods.
        warnings.warn(message, DeprecationWarning, stacklevel=3)
        return

    _warn_at_definition(function, message)


def _warn_at_definition(function: types.FunctionType, message: str) -> None:
    """
    Emit *message* as a :class:`DeprecationWarning` located at the first line of *function*.

    The first line is the ``def`` line, or the first decorator's line for a decorated function.
    The warning registry is the function module's, as with :func:`warnings.warn`.
    """
    code = function.__code__
    warnings.warn_explicit(
        message,
        DeprecationWarning,
        filename=code.co_filename,
        lineno=code.co_firstlineno,
        module=function.__module__,
        registry=function.__globals__.setdefault('__warningregistry__', {}),
    )
