"""
Camera equipment representation extracted from EXIF metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox.compat import override

from .brand import Brand
from .equipment import Equipement

if TYPE_CHECKING:
    from .tag import Tag

__all__ = ['Camera']


class Camera(Equipement):
    """Represent a camera identified from EXIF metadata."""

    brand_class = Brand

    @property
    @override
    def brand(self) -> Brand | None:
        """Return the camera brand from ``Exif.Image.Make``."""
        return self.brand_class(self.metadata['Exif.Image.Make'].data)

    @override
    def _get_tags(self) -> dict[str, Tag]:
        """Return EXIF tags related to the camera."""
        return {k: t for k, t in self.metadata.tags.items() if 'camera' in t.label.lower()}

    @property
    @override
    def _model(self) -> str | None:
        return self.metadata['Exif.Image.Model'].data
