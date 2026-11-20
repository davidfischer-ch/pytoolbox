"""
Photo-level EXIF metadata (exposure, ISO, white balance).
"""

from __future__ import annotations

from datetime import datetime
from fractions import Fraction

from pytoolbox.enum import OrderedEnum, find_member

from .tag import TagSet

__all__ = ['ExposureMode', 'Photo', 'SensingMethod', 'WhiteBalance']


class ExposureMode(OrderedEnum):
    """EXIF exposure mode values (tag Exif.Photo.ExposureMode)."""

    AUTO = 0
    MANUAL = 1
    BRACKET = 2


class SensingMethod(OrderedEnum):
    """EXIF sensing method values (tag Exif.Photo.SensingMethod)."""

    NOT_DEFINED = 0
    UNDEFINED = 1
    ONE_CHIP_COLOR_AREA = 2
    TWO_CHIP_COLOR_AREA = 3
    THREE_CHIP_COLOR_AREA = 4
    COLOR_SEQUENTIAL_AREA = 5
    TRILINEAR = 7
    COLOR_SEQUENTIAL_LINEAR = 8


class WhiteBalance(OrderedEnum):
    """EXIF white balance values (tag Exif.Photo.WhiteBalance)."""

    AUTO = 0
    MANUAL = 1


class Photo(TagSet):
    """Provide access to photo-level EXIF metadata."""

    @property
    def date(self) -> datetime | None:
        """Return the date the photo was taken."""
        return self.metadata.get_date()

    @property
    def exposure_mode(self) -> ExposureMode | None:
        """Return the :class:`ExposureMode` or ``None`` if unknown."""
        return find_member(ExposureMode, self.metadata['Exif.Photo.ExposureMode'].data)

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
    def sensing_method(self) -> SensingMethod | None:
        """Return the :class:`SensingMethod` or ``None`` if unknown."""
        return find_member(SensingMethod, self.metadata['Exif.Photo.SensingMethod'].data)

    @property
    def white_balance(self) -> WhiteBalance | None:
        """Return the :class:`WhiteBalance` or ``None`` if unknown."""
        return find_member(WhiteBalance, self.metadata['Exif.Photo.WhiteBalance'].data)
