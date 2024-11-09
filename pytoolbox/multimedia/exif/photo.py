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
    def date(self) -> datetime.datetime | None:
        return self.metadata.get_date()

    @property
    def exposure_mode(self) -> ExposureMode | None:
        data = self.metadata['Exif.Photo.ExposureMode'].data
        return None if data is None else ExposureMode(data)

    @property
    def exposure_time(self) -> Fraction | None:
        return self.metadata['Exif.Photo.ExposureTime'].data

    @property
    def fnumber(self) -> Fraction | None:
        return self.clean_number(self.metadata['Exif.Photo.FNumber'].data)

    @property
    def focal_length(self) -> Fraction | None:
        return self.clean_number(self.metadata['Exif.Photo.FocalLength'].data)

    @property
    def iso_speed(self) -> int | None:
        return self.clean_number(self.metadata['Exif.Photo.ISOSpeedRatings'].data)

    @property
    def sensing_method(self) -> int | None:
        return self.metadata['Exif.Photo.SensingMethod'].data

    @property
    def white_balance(self) -> int | None:
        return self.metadata['Exif.Photo.WhiteBalance'].data
