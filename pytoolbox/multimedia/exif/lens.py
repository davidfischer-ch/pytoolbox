# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import decorators, module

from . import equipment

_all = module.All(globals())


class Lens(equipment.Equipement):

    @property
    def brand(self):
        brands = set(t.brand for t in self.tags.itervalues() if t.brand)
        if brands:
            assert len(brands) == 1, brands
            return next(iter(brands))

    @property
    def _model(self):
        return next((t.data for t in self.tags.itervalues() if 'model' in t.label.lower()), None)

    @decorators.cached_property
    def tags(self):
        return {k: t for k, t in self.metadata.tags.iteritems() if 'lens' in t.label.lower()}


__all__ = _all.diff(globals())
