"""
Mix-ins for building your own model managers.
"""

from pytoolbox import module
from pytoolbox.django.models import utils
from pytoolbox.django.models.query import mixins as query_mixins

_all = module.All(globals())

AtomicGetUpdateOrCreateMixin = query_mixins.AtomicGetUpdateOrCreateMixin
AtomicGetRestoreOrCreateMixin = query_mixins.AtomicGetRestoreOrCreateMixin
CreateModelMethodMixin = query_mixins.CreateModelMethodMixin
StateMixin = query_mixins.StateMixin


class RelatedModelMixin(object):

    def get_related_manager(self, field):
        return utils.get_related_manager(self.model, field)

    def get_related_model(self, field):
        return utils.get_related_model(self.model, field)


__all__ = _all.diff(globals())
