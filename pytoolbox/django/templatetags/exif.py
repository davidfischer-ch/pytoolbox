"""
EXIF-related template filters.

Each filter renders ``string_if_invalid`` for a value outside its enum.
"""

# pylint:disable=unused-argument
from __future__ import annotations

import enum
from typing import Any, Final, cast

from django.utils.translation import gettext_lazy as _l

from pytoolbox.enum import find_member
from pytoolbox.multimedia.exif.image import Orientation
from pytoolbox.multimedia.exif.photo import ExposureMode, SensingMethod, WhiteBalance

from . import register, string_if_invalid

EXPOSURE_MODE_LABELS: Final[dict[ExposureMode, str]] = cast(
    dict[ExposureMode, str],
    {
        ExposureMode.AUTO: _l('Auto exposure'),
        ExposureMode.MANUAL: _l('Manual exposure'),
        ExposureMode.BRACKET: _l('Auto bracket'),
    },
)

ORIENTATION_LABELS: Final[dict[Orientation, str]] = cast(
    dict[Orientation, str],
    {
        Orientation.NORMAL: _l('Normal orientation'),
        Orientation.HOR_FLIP: _l('Horizontal flip'),
        Orientation.ROT_180_CCW: _l('Rotation 180° CCW'),
        Orientation.VERT_FLIP: _l('Vertical flip'),
        Orientation.HOR_FLIP_ROT_270_CW: _l('Horizontal flip + rotation 270° CW'),
        Orientation.ROT_90_CW: _l('Rotation 90° CW'),
        Orientation.HOR_FLIP_ROT_90_CW: _l('Horizontal flip + rotation 90° CW'),
        Orientation.ROT_270_CW: _l('Rotation 270° CW'),
    },
)

SENSING_METHOD_LABELS: Final[dict[SensingMethod, str]] = cast(
    dict[SensingMethod, str],
    {
        SensingMethod.NOT_DEFINED: _l('Undefined sensing method'),
        SensingMethod.UNDEFINED: _l('Undefined sensing method'),
        SensingMethod.ONE_CHIP_COLOR_AREA: _l('One-chip color area sensing method'),
        SensingMethod.TWO_CHIP_COLOR_AREA: _l('Two-chip color area sensing method'),
        SensingMethod.THREE_CHIP_COLOR_AREA: _l('Three-chip color area sensing method'),
        SensingMethod.COLOR_SEQUENTIAL_AREA: _l('Color sequential area sensing method'),
        SensingMethod.TRILINEAR: _l('Trilinear sensing method'),
        SensingMethod.COLOR_SEQUENTIAL_LINEAR: _l('Color sequential linear sensing method'),
    },
)

WHITE_BALANCE_LABELS: Final[dict[WhiteBalance, str]] = cast(
    dict[WhiteBalance, str],
    {
        WhiteBalance.AUTO: _l('Auto white balance'),
        WhiteBalance.MANUAL: _l('Manual white balance'),
    },
)


@register.filter(is_safe=True)
def exposure_mode(value: int | ExposureMode | None, autoescape: bool = True) -> str:
    """Return the human-readable exposure mode label for the given EXIF integer or enum."""
    return _to_label(ExposureMode, EXPOSURE_MODE_LABELS, value)


@register.filter(is_safe=True)
def orientation(value: int | Orientation | None, autoescape: bool = True) -> str:
    """Return the human-readable orientation label for the given EXIF integer or enum."""
    return _to_label(Orientation, ORIENTATION_LABELS, value)


@register.filter(is_safe=True)
def sensing_method(value: int | SensingMethod | None, autoescape: bool = True) -> str:
    """Return the human-readable sensing method label for the given EXIF integer or enum."""
    return _to_label(SensingMethod, SENSING_METHOD_LABELS, value)


@register.filter(is_safe=True)
def white_balance(value: int | WhiteBalance | None, autoescape: bool = True) -> str:
    """Return the human-readable white balance label for the given EXIF integer or enum."""
    return _to_label(WhiteBalance, WHITE_BALANCE_LABELS, value)


# --- Internals ------------------------------------------------------------------------------------


def _to_label[EnumT: enum.Enum](
    enum_class: type[EnumT],
    labels: dict[EnumT, str],
    value: Any,
) -> str:
    """Return the label of the *enum_class* member holding *value*, else ``string_if_invalid``."""
    if (member := find_member(enum_class, value)) is None:
        return string_if_invalid
    return labels.get(member, string_if_invalid)
