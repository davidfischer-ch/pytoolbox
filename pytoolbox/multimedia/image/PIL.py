"""
Helpers for the :mod:`PIL` (Pillow) image library.
"""

# pylint:disable=invalid-name
from __future__ import annotations

import collections.abc
import functools
from typing import IO, TYPE_CHECKING, Any, Final

from pytoolbox import module

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

_all = module.All(globals())

from PIL import Image  # noqa pylint:disable=wrong-import-order,wrong-import-position

TRANSPOSE_SEQUENCES: Final[dict[int | None, list[Image.Transpose]]] = {
    None: [],
    1: [],
    2: [Image.Transpose.FLIP_LEFT_RIGHT],
    3: [Image.Transpose.ROTATE_180],
    4: [Image.Transpose.FLIP_TOP_BOTTOM],
    5: [Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.ROTATE_90],
    6: [Image.Transpose.ROTATE_270],
    7: [Image.Transpose.FLIP_TOP_BOTTOM, Image.Transpose.ROTATE_90],
    8: [Image.Transpose.ROTATE_90],
}


def get_orientation(
    image: Image.Image,
    orientation_tag: int = 0x0112,
    no_exif_default: int | None = None,
    no_key_default: int | None = None,
) -> int | None:
    """Return the EXIF orientation value of *image*."""
    exif = getattr(image, '_getexif', lambda: None)()
    try:
        return no_exif_default if exif is None else exif[orientation_tag]
    except KeyError:
        return no_key_default


def apply_orientation(  # pylint:disable=dangerous-default-value
    image: Image.Image,
    get_orientation: collections.abc.Callable[  # pylint:disable=redefined-outer-name
        ...,
        int | None,
    ] = get_orientation,
    sequences: dict[int | None, list[Any]] = TRANSPOSE_SEQUENCES,
) -> Image.Image:
    """Credits: https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image."""
    orientation = get_orientation(image)
    return functools.reduce(lambda i, op: i.transpose(op), sequences.get(orientation, []), image)


def open(  # pylint:disable=redefined-builtin
    file_or_path: IO[bytes] | StrOrBytesPath,
) -> Image.Image:
    """Open an image and load it, tolerating truncated files."""
    image = Image.open(file_or_path)
    try:
        image.load()
    except IOError as exc:
        if 'truncated' not in str(exc):
            raise
    return image


def remove_metadata(
    image: Image.Image,
    keys: tuple[str, ...] = ('exif',),
    *,
    inplace: bool = False,
) -> Image.Image:
    """Remove metadata *keys* from *image* info dict."""
    image = image if inplace else image.copy()
    for key in keys:
        if key in image.info:
            image.info[key] = b''
    return image


def remove_transparency(
    image: Image.Image,
    background: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Return a RGB image with an alpha mask applied to picture + background.
    If image is already in RGB, then its a no-op.
    """
    if image.mode == 'RGB':
        return image  # No-op
    alpha = image.convert('RGBA').getchannel('A')
    new_image = Image.new('RGB', image.size, background)
    new_image.paste(image.convert('RGB'), mask=alpha)
    return new_image


def save(image: Image.Image, *args: Any, **kwargs: Any) -> None:
    """Save *image*, preserving EXIF data by default."""
    kwargs.setdefault('exif', image.info.get('exif', b''))
    return image.save(*args, **kwargs)


__all__ = _all.diff(globals())
