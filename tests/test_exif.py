from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Final
import datetime

from pytoolbox.multimedia import exif

DATA_DIRECTORY: Final[Path] = Path(__file__).resolve().parent / 'data'


def test_exif_metadata_on_glusterfs_jpg() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'GlusterFS.jpg')
    assert metadata.camera.brand is None
    assert metadata.camera.model is None
    assert metadata.image.copyright is None
    assert metadata.image.description is None
    assert metadata.image.height == 205
    assert metadata.image.orientation is None
    assert metadata.image.rotation == 0
    assert metadata.image.width == 515
    assert metadata.lens.brand is None
    assert metadata.lens.model is None
    assert metadata.photo.date is None
    assert metadata.photo.exposure_mode is None
    assert metadata.photo.exposure_time is None
    assert metadata.photo.fnumber is None
    assert metadata.photo.focal_length is None
    assert metadata.photo.iso_speed is None
    assert metadata.photo.sensing_method is None
    assert metadata.photo.white_balance is None


def test_exif_metadata_on_david_jpg() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'David.jpg')
    assert metadata.camera.brand is None
    assert metadata.camera.model is None
    assert metadata.image.copyright is None
    assert metadata.image.description == 'aae453fa35cd6400c3ff3110a1f6de8fbb6c0700-0'
    assert metadata.image.height == 256
    assert metadata.image.orientation == exif.Orientation.NORMAL
    assert metadata.image.rotation == 0
    assert metadata.image.width == 256
    assert metadata.lens.brand is None
    assert metadata.lens.model is None
    assert metadata.photo.date == datetime.datetime(2005, 12, 19, 22, 3, 45)
    assert metadata.photo.exposure_mode is None
    assert metadata.photo.fnumber is None
    assert metadata.photo.focal_length is None
    assert metadata.photo.iso_speed is None
    assert metadata.photo.sensing_method is None
    assert metadata.photo.white_balance is None


def test_exif_metadata_on_macro_jpg() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'Macro.jpg')
    assert metadata.camera.brand == 'Canon'
    assert metadata.camera.model == 'EOS 5D Mark II'
    assert metadata.image.copyright == 'David Fischer - david.fischer.ch@gmail.com'
    assert metadata.image.description == '53fb931be149fbb1e644b3b1c27b2e50442cbf0a-0'
    assert metadata.image.height == 3744
    assert metadata.image.orientation == exif.Orientation.NORMAL
    assert metadata.image.rotation == 0
    assert metadata.image.width == 5616
    assert metadata.lens.brand == 'Canon'
    assert metadata.lens.model == 'MP-E65mm f/2.8 1-5x Macro Photo'
    assert metadata.photo.date == datetime.datetime(2012, 8, 3, 17, 34, 57)
    assert metadata.photo.exposure_mode is exif.ExposureMode.MANUAL
    assert metadata.photo.fnumber == Fraction(28, 5)
    assert metadata.photo.focal_length == Fraction(65, 1)
    assert metadata.photo.iso_speed == 100
    assert metadata.photo.sensing_method is None
    assert metadata.photo.white_balance == 0
