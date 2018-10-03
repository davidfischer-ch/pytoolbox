import os, tempfile

import cv2, numpy as np

from pytoolbox.network.http import download_ext


def load_image(path):
    """Reverse channels because OpenCV loads images in BGR mode."""
    return cv2.imread(path, 1)[..., ::-1]


def load_to_file(uri):
    if uri.startswith('http'):
        path = os.path.join(tempfile.gettempdir(), os.path.basename(uri))
        download_ext(uri, path, force=False)
        return path
    return uri


def normalize_rgb(image):
    """Scale integer RGB values [0,255] to float32 [0.0,1.0]."""
    return (image / 255).astype(np.float32)
