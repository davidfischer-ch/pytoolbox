"""
Helpers for the :mod:`PIL` (Pillow) image library.
"""
# pylint:disable=invalid-name
from __future__ import annotations

from typing import Final
import collections.abc
import functools

from pytoolbox import module

_all = module.All(globals())

from PIL import Image  # noqa pylint:disable=wrong-import-position

TRANSPOSE_SEQUENCES: Final[dict[int | None, list[int]]] = {
    # pylint:disable=no-member
    None: [],
    1: [],
    2: [Image.FLIP_LEFT_RIGHT],
    3: [Image.ROTATE_180],
    4: [Image.FLIP_TOP_BOTTOM],
    5: [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],
    6: [Image.ROTATE_270],
    7: [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],
    8: [Image.ROTATE_90]
}


def get_orientation(
    image: Image.Image,
    orientation_tag: int = 0x0112,
    no_exif_default: int | None = None,
    no_key_default: int | None = None
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
        ..., int | None] = get_orientation,
    sequences: dict[int | None, list] = TRANSPOSE_SEQUENCES
) -> Image.Image:
    """Credits: https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image."""
    orientation = get_orientation(image)
    return functools.reduce(lambda i, op: i.transpose(op), sequences.get(orientation, []), image)


def open(file_or_path: object) -> Image.Image:  # pylint:disable=redefined-builtin
    """Open an image and load it, tolerating truncated files."""
    image = Image.open(file_or_path)
    try:
        image.load()
    except IOError as ex:
        if 'truncated' not in str(ex):
            raise
    return image


def remove_metadata(
    image: Image.Image,
    keys: tuple[str, ...] = ('exif',),
    *,
    inplace: bool = False
) -> Image.Image:
    """Remove metadata *keys* from *image* info dict."""
    image = image if inplace else image.copy()
    for key in keys:
        if key in image.info:
            image.info[key] = b''
    return image


def remove_transparency(
    image: Image.Image,
    background: tuple[int, int, int] = (255, 255, 255)
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


def save(image: Image.Image, *args: object, **kwargs: object) -> None:
    """Save *image*, preserving EXIF data by default."""
    kwargs.setdefault('exif', image.info.get('exif', b''))
    return image.save(*args, **kwargs)


__all__ = _all.diff(globals())
