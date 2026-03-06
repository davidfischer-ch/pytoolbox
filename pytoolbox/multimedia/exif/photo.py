"""
Photo-level EXIF metadata (exposure, ISO, white balance).
"""
from __future__ import annotations

import datetime
from fractions import Fraction

from pytoolbox.enum import OrderedEnum

from .tag import TagSet

__all__ = ['ExposureMode', 'Photo']


class ExposureMode(OrderedEnum):
    """EXIF exposure mode values."""
    AUTO = 0
    MANUAL = 1
    BRACKET = 2


class Photo(TagSet):
    """Provide access to photo-level EXIF metadata."""

    @property
    def date(self) -> datetime.datetime | None:
        """Return the date the photo was taken."""
        return self.metadata.get_date()

    @property
    def exposure_mode(self) -> ExposureMode | None:
        """Return the :class:`ExposureMode` or ``None``."""
        data = self.metadata['Exif.Photo.ExposureMode'].data
        return None if data is None else ExposureMode(data)

    @property
    def exposure_time(self) -> Fraction | None:
        """Return the exposure time as a :class:`~fractions.Fraction`."""
        return self.metadata['Exif.Photo.ExposureTime'].data

    @property
    def fnumber(self) -> Fraction | None:
        """Return the F-number (aperture)."""
        return self.clean_number(self.metadata['Exif.Photo.FNumber'].data)

    @property
    def focal_length(self) -> Fraction | None:
        """Return the focal length."""
        return self.clean_number(self.metadata['Exif.Photo.FocalLength'].data)

    @property
    def iso_speed(self) -> int | None:
        """Return the ISO speed rating."""
        return self.clean_number(self.metadata['Exif.Photo.ISOSpeedRatings'].data)

    @property
    def sensing_method(self) -> int | None:
        """Return the sensing method identifier."""
        return self.metadata['Exif.Photo.SensingMethod'].data

    @property
    def white_balance(self) -> int | None:
        """Return the white balance mode identifier."""
        return self.metadata['Exif.Photo.WhiteBalance'].data
