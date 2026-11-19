"""
Helper functions for loading and normalizing images.
"""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path

import cv2
import numpy as np

from pytoolbox.network.http import download_ext


def load_image(path: str) -> np.ndarray:
    """Reverse channels because OpenCV loads images in BGR mode."""
    image = cv2.imread(path, 1)  # pylint:disable=no-member
    if image is None:
        raise ValueError(f'Unable to load the image {path}')
    return image[..., ::-1]


def load_to_file(uri: str) -> str:
    """
    Download a remote URI to a local temp file, or return the path as-is.

    The file is cached in ``<tmp>/pytoolbox-<uid>``, which must be a directory the user owns with
    no access for the group or others; :class:`PermissionError` otherwise.
    """
    if uri.startswith('http'):
        path = _private_cache_directory() / Path(uri).name
        download_ext(uri, path, force=False)
        return str(path)
    return uri


def normalize_rgb(image: np.ndarray) -> np.ndarray:
    """Scale integer RGB values [0,255] to float32 [0.0,1.0]."""
    return (image / 255).astype(np.float32)


# --- Internals ------------------------------------------------------------------------------------


def _private_cache_directory() -> Path:
    """Return the user's directory in the temporary one, created with access for the user alone."""
    directory = Path(tempfile.gettempdir()) / f'pytoolbox-{os.getuid()}'
    with contextlib.suppress(FileExistsError):
        directory.mkdir(mode=0o700)
    status = directory.lstat()
    if not stat.S_ISDIR(status.st_mode) or status.st_uid != os.getuid() or status.st_mode & 0o077:
        raise PermissionError(f'Directory {directory} is not private to the user')
    return directory
