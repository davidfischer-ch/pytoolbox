"""EXIF-related template filters."""
# pylint:disable=unused-argument
from __future__ import annotations

from typing import Final, cast

from django.utils.translation import gettext_lazy as _l

from pytoolbox.multimedia.exif.image import Orientation
from pytoolbox.multimedia.exif.photo import ExposureMode, SensingMethod, WhiteBalance

from . import register, string_if_invalid

EXPOSURE_MODE_LABELS: Final[dict[ExposureMode, str]] = cast(dict[ExposureMode, str], {
    ExposureMode.AUTO: _l('Auto exposure'),
    ExposureMode.MANUAL: _l('Manual exposure'),
    ExposureMode.BRACKET: _l('Auto bracket')
})

ORIENTATION_LABELS: Final[dict[Orientation, str]] = cast(dict[Orientation, str], {
    Orientation.NORMAL: _l('Normal orientation'),
    Orientation.HOR_FLIP: _l('Horizontal flip'),
    Orientation.ROT_180_CCW: _l('Rotation 180° CCW'),
    Orientation.VERT_FLIP: _l('Vertical flip'),
    Orientation.HOR_FLIP_ROT_270_CW: _l('Horizontal flip + rotation 270° CW'),
    Orientation.ROT_90_CW: _l('Rotation 90° CW'),
    Orientation.HOR_FLIP_ROT_90_CW: _l('Horizontal flip + rotation 90° CW'),
    Orientation.ROT_270_CW: _l('Rotation 270° CW')
})

SENSING_METHOD_LABELS: Final[dict[SensingMethod, str]] = cast(dict[SensingMethod, str], {
    SensingMethod.NOT_DEFINED: _l('Undefined sensing method'),
    SensingMethod.UNDEFINED: _l('Undefined sensing method'),
    SensingMethod.ONE_CHIP_COLOR_AREA: _l('One-chip color area sensing method'),
    SensingMethod.TWO_CHIP_COLOR_AREA: _l('Two-chip color area sensing method'),
    SensingMethod.THREE_CHIP_COLOR_AREA: _l('Three-chip color area sensing method'),
    SensingMethod.COLOR_SEQUENTIAL_AREA: _l('Color sequential area sensing method'),
    SensingMethod.TRILINEAR: _l('Trilinear sensing method'),
    SensingMethod.COLOR_SEQUENTIAL_LINEAR: _l('Color sequential linear sensing method')
})

WHITE_BALANCE_LABELS: Final[dict[WhiteBalance, str]] = cast(dict[WhiteBalance, str], {
    WhiteBalance.AUTO: _l('Auto white balance'),
    WhiteBalance.MANUAL: _l('Manual white balance')
})


@register.filter(is_safe=True)
def exposure_mode(value: int | ExposureMode | None, autoescape: bool = True) -> str:
    """Return the human-readable exposure mode label for the given EXIF integer or enum."""
    if value in (None, string_if_invalid):
        return string_if_invalid
    if not isinstance(value, ExposureMode):
        value = ExposureMode(value)
    return EXPOSURE_MODE_LABELS.get(value, string_if_invalid)


@register.filter(is_safe=True)
def orientation(value: int | Orientation | None, autoescape: bool = True) -> str:
    """Return the human-readable orientation label for the given EXIF integer or enum."""
    if value in (None, string_if_invalid):
        return string_if_invalid
    if not isinstance(value, Orientation):
        value = Orientation(value)
    return ORIENTATION_LABELS.get(value, string_if_invalid)


@register.filter(is_safe=True)
def sensing_method(value: int | SensingMethod | None, autoescape: bool = True) -> str:
    """Return the human-readable sensing method label for the given EXIF integer or enum."""
    if value in (None, string_if_invalid):
        return string_if_invalid
    if not isinstance(value, SensingMethod):
        value = SensingMethod(value)
    return SENSING_METHOD_LABELS.get(value, string_if_invalid)


@register.filter(is_safe=True)
def white_balance(value: int | WhiteBalance | None, autoescape: bool = True) -> str:
    """Return the human-readable white balance label for the given EXIF integer or enum."""
    if value in (None, string_if_invalid):
        return string_if_invalid
    if not isinstance(value, WhiteBalance):
        value = WhiteBalance(value)
    return WHITE_BALANCE_LABELS.get(value, string_if_invalid)
