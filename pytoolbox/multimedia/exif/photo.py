# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

try:
    from pytoolbox.enum import OrderedEnum

    class ExposureMode(OrderedEnum):
        AUTO = 0
        MANUAL = 1
        BRACKET = 2
except ImportError:
    ExposureMode = {0: 'auto', 1: 'manual', 2: 'bracket'}.get

from . import tag


_all = module.All(globals())


class Photo(tag.TagSet):

    @property
    def date(self):
        return self.metadata.get_date()

    @property
    def exposure_mode(self):
        return ExposureMode(self.metadata['Exif.Photo.ExposureMode'].data)

    @property
    def exposure_time(self):
        return self.metadata['Exif.Photo.ExposureTime'].data

    @property
    def fnumber(self):
        return self.clean_number(self.metadata['Exif.Photo.FNumber'].data)

    @property
    def focal_length(self):
        return self.clean_number(self.metadata['Exif.Photo.FocalLength'].data)

    @property
    def iso_speed(self):
        return self.clean_number(self.metadata['Exif.Photo.ISOSpeedRatings'].data)

    @property
    def sensing_method(self):
        return self.metadata['Exif.Photo.SensingMethod'].data

    @property
    def white_balance(self):
        return self.metadata['Exif.Photo.WhiteBalance'].data


__all__ = _all.diff(globals())
