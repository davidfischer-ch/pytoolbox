from .types import get_slots

__all__ = ['SlotsEqualityMixin']


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
