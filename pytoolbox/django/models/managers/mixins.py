# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own model managers.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from .. import utils
from ..query import mixins as query_mixins
from .... import module

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
