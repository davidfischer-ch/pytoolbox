"""
Mix-ins for building your own `Django Filter <https://github.com/alex/django-filter>`_
powered filters.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox.compat import override

if TYPE_CHECKING:
    from django.db.models import Field
    from django_filters import Filter, FilterSet

# The mixin completes a FilterSet; naming the base under TYPE_CHECKING states that requirement for
# the checker only.
_FilterSetMixin = FilterSet if TYPE_CHECKING else object

__all__ = ['RaiseOnUnhandledFieldClassMixin']


class RaiseOnUnhandledFieldClassMixin(_FilterSetMixin):
    """
    Raise an exception when the filter set is unable to find a suitable filter for any of the model
    fields to filter.
    """

    @classmethod
    @override
    def filter_for_field(cls, f: Field, name: str, lookup_type: str = 'exact') -> Filter:
        """Return a filter for the field, raising if none is found."""
        value = super().filter_for_field(f, name, lookup_type)
        if not value:
            raise NotImplementedError(
                f"Unable to find a suitable filter for field '{name}' of class {type(f)} "
                f"with lookup type '{lookup_type}'",
            )
        return value
