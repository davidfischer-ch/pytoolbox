from __future__ import annotations

import datetime
from fractions import Fraction

from pytoolbox.enum import OrderedEnum

from .tag import TagSet

__all__ = ['ExposureMode', 'Photo']


class ExposureMode(OrderedEnum):
    AUTO = 0
    MANUAL = 1
    BRACKET = 2


class Photo(TagSet):

    @property
    def date(self) -> datetime.datetime:
        return self.metadata.get_date()

    @property
    def exposure_mode(self) -> ExposureMode:
        return ExposureMode(self.metadata['Exif.Photo.ExposureMode'].data)

    @property
    def exposure_time(self) -> Fraction | None:
        value = self.metadata['Exif.Photo.ExposureTime'].data
        assert value is None or isinstance(value, Fraction), type(value)
        return value

    @property
    def fnumber(self) -> Fraction | None:
        value = self.clean_number(self.metadata['Exif.Photo.FNumber'].data)
        assert value is None or isinstance(value, Fraction), type(value)
        return value

    @property
    def focal_length(self) -> Fraction | None:
        value = self.clean_number(self.metadata['Exif.Photo.FocalLength'].data)
        assert value is None or isinstance(value, Fraction), type(value)
        return value

    @property
    def iso_speed(self) -> int | None:
        value = self.clean_number(self.metadata['Exif.Photo.ISOSpeedRatings'].data)
        assert value is None or isinstance(value, int), type(value)
        return value

    @property
    def sensing_method(self) -> int | None:
        value = self.metadata['Exif.Photo.SensingMethod'].data
        assert value is None or isinstance(value, int), type(value)
        return value

    @property
    def white_balance(self) -> int | None:
        value = self.metadata['Exif.Photo.WhiteBalance'].data
        assert value is None or isinstance(value, int), type(value)
        return value
