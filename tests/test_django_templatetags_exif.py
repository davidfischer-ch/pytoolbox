from __future__ import annotations

from pytoolbox.django import templatetags
from pytoolbox.multimedia.exif.image import Orientation
from pytoolbox.multimedia.exif.photo import ExposureMode, SensingMethod, WhiteBalance


def test_exposure_mode_int() -> None:
    """Integer input is converted to enum and returns the translated label."""
    assert templatetags.exposure_mode(0) == 'Auto exposure'
    assert templatetags.exposure_mode(1) == 'Manual exposure'
    assert templatetags.exposure_mode(2) == 'Auto bracket'


def test_exposure_mode_enum() -> None:
    """Enum input is accepted directly and returns the translated label."""
    assert templatetags.exposure_mode(ExposureMode.AUTO) == 'Auto exposure'
    assert templatetags.exposure_mode(ExposureMode.MANUAL) == 'Manual exposure'


def test_exposure_mode_none() -> None:
    """None returns the invalid string marker."""
    assert templatetags.exposure_mode(None) == templatetags.string_if_invalid


def test_orientation_int() -> None:
    """Integer input is converted to enum and returns the translated label."""
    assert templatetags.orientation(1) == 'Normal orientation'
    assert templatetags.orientation(6) == 'Rotation 90° CW'
    assert templatetags.orientation(8) == 'Rotation 270° CW'


def test_orientation_enum() -> None:
    """Enum input is accepted directly and returns the translated label."""
    assert templatetags.orientation(Orientation.NORMAL) == 'Normal orientation'
    assert templatetags.orientation(Orientation.HOR_FLIP) == 'Horizontal flip'


def test_orientation_none() -> None:
    """None returns the invalid string marker."""
    assert templatetags.orientation(None) == templatetags.string_if_invalid


def test_sensing_method_int() -> None:
    """Integer input is converted to enum and returns the translated label."""
    assert templatetags.sensing_method(2) == 'One-chip color area sensing method'
    assert templatetags.sensing_method(7) == 'Trilinear sensing method'


def test_sensing_method_enum() -> None:
    """Enum input is accepted directly and returns the translated label."""
    label = templatetags.sensing_method(SensingMethod.ONE_CHIP_COLOR_AREA)
    assert label == 'One-chip color area sensing method'


def test_sensing_method_none() -> None:
    """None returns the invalid string marker."""
    assert templatetags.sensing_method(None) == templatetags.string_if_invalid


def test_white_balance_int() -> None:
    """Integer input is converted to enum and returns the translated label."""
    assert templatetags.white_balance(0) == 'Auto white balance'
    assert templatetags.white_balance(1) == 'Manual white balance'


def test_white_balance_enum() -> None:
    """Enum input is accepted directly and returns the translated label."""
    assert templatetags.white_balance(WhiteBalance.AUTO) == 'Auto white balance'
    assert templatetags.white_balance(WhiteBalance.MANUAL) == 'Manual white balance'


def test_white_balance_none() -> None:
    """None returns the invalid string marker."""
    assert templatetags.white_balance(None) == templatetags.string_if_invalid
