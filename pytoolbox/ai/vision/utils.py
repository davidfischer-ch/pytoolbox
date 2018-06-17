import cv2, numpy as np


def load_image(path):
    """Reverse channels because OpenCV loads images in BGR mode."""
    return cv2.imread(path, 1)[..., ::-1]


def normalize_rgb(image):
    """Scale integer RGB values [0,255] to float32 [0.0,1.0]."""
    return (image / 255).astype(np.float32)
