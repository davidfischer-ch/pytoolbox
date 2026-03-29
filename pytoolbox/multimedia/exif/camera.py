"""
Camera equipment representation extracted from EXIF metadata.
"""

from __future__ import annotations

from pytoolbox import decorators

from .brand import Brand
from .equipment import Equipement

__all__ = ['Camera']


class Camera(Equipement):
    """Represent a camera identified from EXIF metadata."""

    brand_class = Brand

    @property
    def brand(self) -> Brand:
        """Return the camera brand from ``Exif.Image.Make``."""
        return self.brand_class(self.metadata['Exif.Image.Make'].data)

    @decorators.cached_property
    def tags(self) -> dict:  # type: ignore[override]  # pylint: disable=invalid-overridden-method
        """Return EXIF tags related to the camera."""
        return {k: t for k, t in self.metadata.tags.items() if 'camera' in t.label.lower()}

    @property
    def _model(self) -> str:
        return self.metadata['Exif.Image.Model'].data
