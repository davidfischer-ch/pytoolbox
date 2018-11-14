# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import decorators, module

from . import brand, equipment

_all = module.All(globals())


class Camera(equipment.Equipement):

    brand_class = brand.Brand

    @property
    def brand(self):
        return self.brand_class(self.metadata['Exif.Image.Make'].data)

    @property
    def _model(self):
        return self.metadata['Exif.Image.Model'].data

    @decorators.cached_property
    def tags(self):
        return {k: t for k, t in self.metadata.tags.iteritems() if 'camera' in t.label.lower()}


__all__ = _all.diff(globals())
