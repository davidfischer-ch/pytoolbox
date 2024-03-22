"""
Mix-ins for building your own `Django Filter <https://github.com/alex/django-filter>`_
powered filters.
"""
from __future__ import annotations

__all__ = ['RaiseOnUnhandledFieldClassMixin']


class RaiseOnUnhandledFieldClassMixin(object):
    """
    Raise an exception when the filter set is unable to find a suitable filter for any of the model
    fields to filter.
    """

    @classmethod
    def filter_for_field(cls, f, name, *, lookup_type='exact'):
        value = super().filter_for_field(f, name, lookup_type)
        if not value:
            raise NotImplementedError(
                f"Unable to find a suitable filter for field '{name}' of class {f.__class__} "
                f"with lookup type '{lookup_type}'")
        return value
