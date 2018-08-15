# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from . import module
from .types import get_slots

_all = module.All(globals())


class SlotsEqualityMixin(object):
    """
    Implement the comparison operators based on the slots. Both the name of the slots retrieved with
    :func:`pytoolbox.types.get_slots` and theirs values are tested for equality.
    """

    def __eq__(self, other):
        return get_slots(self) == get_slots(other) and \
            all(getattr(self, attr) == getattr(other, attr) for attr in get_slots(self))

    def __ne__(self, other):
        return not self.__eq__(other)


__all__ = _all.diff(globals())
