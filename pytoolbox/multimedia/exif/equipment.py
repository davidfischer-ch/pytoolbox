"""
Abstract base class for photographic equipment (cameras and lenses).
"""

from __future__ import annotations

import abc
import re
from typing import TYPE_CHECKING

from pytoolbox import decorators

from .brand import Brand

if TYPE_CHECKING:
    from .metadata import Metadata
    from .tag import Tag

__all__ = ['Equipement']


class Equipement(metaclass=abc.ABCMeta):
    """Abstract base for photographic equipment identified from EXIF data."""

    def __init__(self, metadata: Metadata) -> None:
        self.metadata = metadata

    def __bool__(self) -> bool:
        return bool(self.model)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Equipement):
            return NotImplemented
        return self.brand == other.brand and self.model == other.model

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f'<{type(self).__name__} {self.brand} {self.model}>'

    @property
    @abc.abstractmethod
    def brand(self) -> Brand | None:
        """Return the equipment brand."""

    @property
    def model(self) -> str | None:
        """Return the model name with the brand prefix stripped."""
        if self.brand and self._model:
            return re.sub(rf'{self.brand}\s+', '', self._model, count=1, flags=re.IGNORECASE)
        return self._model

    @decorators.cached_property
    def tags(self) -> dict[str, Tag]:
        """Return EXIF tags related to this equipment."""
        return self._get_tags()

    def refresh(self) -> None:
        """Clear cached tags so they are recomputed on next access."""
        self.__dict__.pop('tags', None)

    @abc.abstractmethod
    def _get_tags(self) -> dict[str, Tag]:
        """Return the EXIF tags describing this equipment."""

    @property
    @abc.abstractmethod
    def _model(self) -> str | None:
        pass
