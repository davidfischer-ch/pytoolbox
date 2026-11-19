"""
Mix-ins for building your own `Django Filter <https://github.com/alex/django-filter>`_
powered filters.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django_filters import FilterSet

# The mixin completes a FilterSet; naming the base under TYPE_CHECKING states that requirement for
# the checker only.
_FilterSetMixin = FilterSet if TYPE_CHECKING else object

__all__ = ['RaiseOnUnhandledFieldClassMixin']


class RaiseOnUnhandledFieldClassMixin(_FilterSetMixin):
    """
    Empty mix-in: :class:`~django_filters.FilterSet` raises on a model field no filter class
    matches, by default (``Meta.unknown_field_behavior``).

    .. deprecated:: 14.13.0
       Use :class:`~django_filters.FilterSet` instead.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            'RaiseOnUnhandledFieldClassMixin is deprecated; use django_filters.FilterSet, '
            'which raises on an unhandled field by default (Meta.unknown_field_behavior).',
            DeprecationWarning,
            stacklevel=3,  # The subclass statement, past FilterSetMetaclass.__new__.
        )
