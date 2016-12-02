# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from ...enum import OrderedEnum

    class Orientation(OrderedEnum):
        NORMAL = 1
        HOR_FLIP = 2
        ROT_180_CCW = 3
        VERT_FLIP = 4
        HOR_FLIP_ROT_270_CW = 5
        ROT_90_CW = 6
        HOR_FLIP_ROT_90_CW = 7
        ROT_270_CW = 8
except ImportError:
    Orientation = lambda x: xrange(1, 9)[x-1]  # noqa

from . import tag
from ... import module

_all = module.All(globals())


class Image(tag.TagSet):

    @property
    def copyright(self):
        return self.metadata['Iptc.Application2.Copyright'].data

    @property
    def description(self):
        return self.metadata['Exif.Image.ImageDescription'].data

    @property
    def height(self):
        return self.clean_number(self.metadata.exiv2.get_pixel_height())

    @property
    def orientation(self):
        data = self.metadata['Exif.Image.Orientation'].data
        try:
            return Orientation(data)
        except:
            return None

    @property
    def width(self):
        return self.clean_number(self.metadata.exiv2.get_pixel_width())

__all__ = _all.diff(globals())
