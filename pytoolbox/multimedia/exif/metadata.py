# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

from . import camera, image, lens, photo, tag
from ... import module
from ...encoding import string_types

_all = module.All(globals())


class Metadata(object):

    tag_class = tag.Tag

    def __init__(self, path):
        from gi.repository import GExiv2
        self.path = path
        self.exiv2 = GExiv2.Metadata()
        self.exiv2.open_path(path)
        self.camera = camera.Camera(self)
        self.image = image.Image(self)
        self.lens = lens.Lens(self)
        self.photo = photo.Photo(self)

    def __getitem__(self, key):
        # FIXME make it more strict and re-implement less strict self.get(key)
        return self.tag_class(self, key)

    def __setitem__(self, key, value):
        self.exiv2[key] = value

    @property
    def tags(self):
        return {k: self[k] for k in self.exiv2.get_tags()}

    def get_date(self, keys=('Exif.Photo.DateTimeOriginal', 'Exif.Image.DateTime'), fail=True):
        for key in ([keys] if isinstance(keys, string_types) else keys):
            date = self[key].data
            if isinstance(date, datetime.datetime):
                return date

    def save_file(self):
        return self.exiv2.save_file()

__all__ = _all.diff(globals())
