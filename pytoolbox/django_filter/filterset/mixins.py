"""
Mix-ins for building your own `Django Filter <https://github.com/alex/django-filter>`_
powered filters.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Field
    from django_filters import Filter

__all__ = ['RaiseOnUnhandledFieldClassMixin']


class RaiseOnUnhandledFieldClassMixin:
    """
    Raise an exception when the filter set is unable to find a suitable filter for any of the model
    fields to filter.
    """

    @classmethod
    def filter_for_field(cls, f: Field, name: str, *, lookup_type: str = 'exact') -> Filter:
        """Return a filter for the field, raising if none is found."""
        value = super().filter_for_field(f, name, lookup_type)
        if not value:
            raise NotImplementedError(
                f"Unable to find a suitable filter for field '{name}' of class {type(f)} "
                f"with lookup type '{lookup_type}'")
        return value
