# -*- encoding: utf-8 -*-

from PIL import Image


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
    """Return a RGB image with an alpha mask applied to picture + background. Do nothing if alpha not found."""
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = (image.convert('RGBA') if image.mode == 'LA' else image).split()[-1]
        new_image = Image.new('RGB', image.size, background)
        new_image.paste(image, mask=alpha)
        return new_image
    return image


def save(image, *args, **kwargs):
    kwargs.setdefault('exif', image.info.get('exif', b''))
    return image.save(*args, **kwargs)
