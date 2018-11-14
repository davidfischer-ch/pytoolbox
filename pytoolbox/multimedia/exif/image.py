# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

try:
    import enum
    _Enum = enum.Enum
except ImportError:
    _Enum = object

from . import tag

_all = module.All(globals())


class Orientation(_Enum):
    NORMAL = 1
    HOR_FLIP = 2
    ROT_180_CCW = 3
    VERT_FLIP = 4
    HOR_FLIP_ROT_270_CW = 5
    ROT_90_CW = 6
    HOR_FLIP_ROT_90_CW = 7
    ROT_270_CW = 8


class Image(tag.TagSet):

    ORIENTATION_TO_ROTATION = {
        None: 0,
        Orientation.NORMAL: 0,
        # 2 = Mirror horizontal
        Orientation.ROT_180_CCW: 180,
        # 4 = Mirror vertical
        # 5 = Mirror horizontal and rotate 270 CW
        Orientation.ROT_90_CW: -90,
        # 7 = Mirror horizontal and rotate 90 CW
        Orientation.ROT_270_CW: -270
    }

    def __init__(self, metadata, orientation=None):
        super(Image, self).__init__(metadata)
        self._orientation = None if orientation is None else Orientation(orientation)

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
        if self._orientation is not None:
            return self._orientation
        data = self.metadata['Exif.Image.Orientation'].data
        try:
            return Orientation(data)
        except:
            return None

    @property
    def rotation(self):
        return self.ORIENTATION_TO_ROTATION[self.orientation]

    @property
    def width(self):
        return self.clean_number(self.metadata.exiv2.get_pixel_width())


__all__ = _all.diff(globals())
