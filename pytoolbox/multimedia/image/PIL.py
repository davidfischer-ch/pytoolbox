# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import functools

from pytoolbox import module

_all = module.All(globals())

from PIL import Image  # noqa

TRANSPOSE_SEQUENCES = {
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


def get_orientation(image, orientation_tag=0x0112, no_exif_default=None, no_key_default=None):
    exif = getattr(image, '_getexif', lambda: None)()
    try:
        return no_exif_default if exif is None else exif[orientation_tag]
    except KeyError:
        return no_key_default


def apply_orientation(image, get_orientation=get_orientation, sequences=TRANSPOSE_SEQUENCES):
    """Credits: https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image."""
    orientation = get_orientation(image)
    return functools.reduce(lambda i, op: i.transpose(op), sequences.get(orientation, []), image)


def open(file_or_path):
    image = Image.open(file_or_path)
    try:
        image.load()
    except IOError as e:
        if 'truncated' not in str(e):
            raise
    return image


def remove_metadata(image, keys=('exif', ), inplace=False):
    image = image if inplace else image.copy()
    for key in keys:
        if key in image.info:
            image.info[key] = b''
    return image


def remove_transparency(image, background=(255, 255, 255)):
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


def save(image, *args, **kwargs):
    kwargs.setdefault('exif', image.info.get('exif', b''))
    return image.save(*args, **kwargs)


__all__ = _all.diff(globals())
