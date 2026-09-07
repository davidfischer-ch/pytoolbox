"""
Lens equipment representation extracted from EXIF metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox.compat import override

from .brand import Brand
from .equipment import Equipement

if TYPE_CHECKING:
    from .tag import Tag

__all__ = ['Lens']


class Lens(Equipement):
    """Represent a lens identified from EXIF metadata."""

    brand_class = Brand

    @property
    @override
    def brand(self) -> Brand | None:
        """Return the lens brand inferred from tags or model name."""
        if brands := {t.brand for t in self.tags.values() if t.brand}:
            assert len(brands) == 1, brands
            return next(iter(brands))
        # Extract brand from model
        model = self._model
        return self.brand_class(model.split(' ')[0]) if model else None

    @property
    @override
    def _model(self) -> str | None:
        return next((t.data for t in self.tags.values() if 'model' in t.label.lower()), None)

    @override
    def _get_tags(self) -> dict[str, Tag]:
        """Return EXIF tags related to the lens."""
        return {k: t for k, t in self.metadata.tags.items() if 'lens' in t.label.lower()}
