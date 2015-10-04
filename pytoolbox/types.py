# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import inspect
try:
    from collections import abc
except ImportError:
    import collections as abc
import itertools

from . import module
from .encoding import binary_type, string_types

_all = module.All(globals())


def get_properties(obj):
    return ((n, getattr(obj, n)) for n, p in inspect.getmembers(obj.__class__, lambda m: isinstance(m, property)))


def get_slots(obj):
    """Return a set with the `__slots__` of the `obj` including all parent classes `__slots__`."""
    return set(itertools.chain.from_iterable(getattr(cls, '__slots__', ()) for cls in obj.__class__.__mro__))


def isiterable(obj, blacklist=(binary_type, string_types)):
    """
    Return ``True`` if the object is an iterable, but ``False`` for any class in `blacklist`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> for obj in 'text', b'binary', u'unicode', 42:
    ...     asserts.false(isiterable(obj), obj)
    >>> for obj in [], (), set(), {}.iteritems():
    ...     asserts.true(isiterable(obj), obj)
    ...     asserts.false(isiterable({}, dict))
    """
    return isinstance(obj, abc.Iterable) and not isinstance(obj, blacklist)


class DummyObject(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MissingType(object):

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __nonzero__(self):
        return False

    def __repr__(self):
        return 'Missing'


Missing = MissingType()

__all__ = _all.diff(globals())
