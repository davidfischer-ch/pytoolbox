"""
Mix-ins for building your own model managers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox import module
from pytoolbox.django.models import utils
from pytoolbox.django.models.query import mixins as query_mixins

if TYPE_CHECKING:
    from django.db import models

_all = module.All(globals())

AtomicGetUpdateOrCreateMixin = query_mixins.AtomicGetUpdateOrCreateMixin
AtomicGetRestoreOrCreateMixin = query_mixins.AtomicGetRestoreOrCreateMixin
CreateModelMethodMixin = query_mixins.CreateModelMethodMixin
StateMixin = query_mixins.StateMixin


class RelatedModelMixin:
    """Provide shortcuts to access related model classes and managers."""

    def get_related_manager(self, field: str) -> models.Manager:
        """Return the default manager for the model related through *field*."""
        return utils.get_related_manager(self.model, field)

    def get_related_model(self, field: str) -> type[models.Model]:
        """Return the model class related through *field*."""
        return utils.get_related_model(self.model, field)


__all__ = _all.diff(globals())
