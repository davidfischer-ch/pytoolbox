from __future__ import annotations

import datetime
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Final

import pytest

from pytoolbox import exceptions
from pytoolbox.multimedia import exif
from pytoolbox.multimedia.exif.tag import Tag

DATA_DIRECTORY: Final[Path] = Path(__file__).resolve().parent / 'data'

_gexiv2_available = False
try:
    import gi as _gi

    _gi.require_version('GExiv2', '0.10')
    from gi.repository import GExiv2 as _GExiv2  # noqa: F401

    _gexiv2_available = True
except (ImportError, ValueError):
    pass

requires_gexiv2 = pytest.mark.skipif(not _gexiv2_available, reason='GExiv2 not available')


@requires_gexiv2
def test_metadata_get_date_with_single_key() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'Macro.jpg')
    result = metadata.get_date(keys=['Exif.Photo.DateTimeOriginal'])
    assert result == datetime.datetime(2012, 8, 3, 17, 34, 57)


@requires_gexiv2
def test_metadata_getitem_returns_tag() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'Macro.jpg')
    tag = metadata['Exif.Image.Make']
    assert isinstance(tag, Tag)
    assert tag.key == 'Exif.Image.Make'


@requires_gexiv2
def test_metadata_init_with_buf() -> None:
    buf = (DATA_DIRECTORY / 'Macro.jpg').read_bytes()
    metadata = exif.Metadata(buf=buf)
    assert metadata.path is None


@requires_gexiv2
def test_metadata_init_without_path_or_buf_raises() -> None:
    with pytest.raises(ValueError):
        exif.Metadata()


@requires_gexiv2
def test_metadata_on_david_jpg() -> None:
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


@requires_gexiv2
def test_metadata_on_glusterfs_jpg() -> None:
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


@requires_gexiv2
def test_metadata_on_macro_jpg() -> None:
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
    assert metadata.photo.white_balance is exif.WhiteBalance.AUTO


@requires_gexiv2
def test_metadata_rewrite(tmp_path: Path) -> None:
    dst = tmp_path / 'GlusterFS.jpg'
    shutil.copy(DATA_DIRECTORY / 'GlusterFS.jpg', dst)
    metadata = exif.Metadata(path=dst)
    metadata.rewrite(save=True)
    reloaded = exif.Metadata(path=dst)
    assert reloaded.image.width == 515
    assert reloaded.image.height == 205


@requires_gexiv2
def test_metadata_save_file_no_path_raises() -> None:
    buf = (DATA_DIRECTORY / 'Macro.jpg').read_bytes()
    metadata = exif.Metadata(buf=buf)
    with pytest.raises(exceptions.UndefinedPathError):
        metadata.save_file()


@requires_gexiv2
def test_metadata_save_file_uses_self_path(tmp_path: Path) -> None:
    dst = tmp_path / 'Macro.jpg'
    shutil.copy(DATA_DIRECTORY / 'Macro.jpg', dst)
    metadata = exif.Metadata(path=dst)
    metadata.save_file()
    reloaded = exif.Metadata(path=dst)
    assert reloaded.camera.brand == 'Canon'


@requires_gexiv2
def test_metadata_save_file_with_explicit_path(tmp_path: Path) -> None:
    copy = tmp_path / 'Macro.jpg'
    other = tmp_path / 'other.jpg'
    shutil.copy(DATA_DIRECTORY / 'Macro.jpg', copy)
    shutil.copy(DATA_DIRECTORY / 'Macro.jpg', other)
    metadata = exif.Metadata(path=copy)
    metadata.save_file(path=other)
    reloaded = exif.Metadata(path=other)
    assert reloaded.camera.brand == 'Canon'


@requires_gexiv2
def test_metadata_setitem(tmp_path: Path) -> None:
    dst = tmp_path / 'Macro.jpg'
    shutil.copy(DATA_DIRECTORY / 'Macro.jpg', dst)
    metadata = exif.Metadata(path=dst)
    metadata['Exif.Image.ImageDescription'] = 'new-description'
    metadata.save_file()
    reloaded = exif.Metadata(path=dst)
    assert reloaded['Exif.Image.ImageDescription'].data == 'new-description'


@requires_gexiv2
def test_metadata_setitem_without_type_hook_raises() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'Macro.jpg')
    with pytest.raises(NotImplementedError):
        metadata['Exif.Photo.MakerNote'] = b'raw data'


@requires_gexiv2
def test_metadata_tags_returns_dict_of_tags() -> None:
    metadata = exif.Metadata(path=DATA_DIRECTORY / 'Macro.jpg')
    tags = metadata.tags
    assert 'Exif.Image.Make' in tags
    assert all(isinstance(v, Tag) for v in tags.values())
