"""
Abstract base class for photographic equipment (cameras and lenses).
"""

from __future__ import annotations

import abc
import re

from .brand import Brand

__all__ = ['Equipement']


class Equipement(metaclass=abc.ABCMeta):
    """Abstract base for photographic equipment identified from EXIF data."""

    def __init__(self, metadata: object) -> None:
        self.metadata = metadata

    def __bool__(self) -> bool:
        return bool(self.model)

    def __eq__(self, other: object) -> bool:
        try:
            return self.brand == other.brand and self.model == other.model
        except AttributeError:
            return NotImplemented

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
            return re.sub(rf'{self.brand}\s+', '', self._model, 1, re.IGNORECASE)
        return self._model

    @property
    @abc.abstractmethod
    def tags(self) -> dict:
        """Return EXIF tags related to this equipment."""

    def refresh(self) -> None:
        """Clear cached tags so they are recomputed on next access."""
        self.__dict__.pop('tags', None)

    @property
    @abc.abstractmethod
    def _model(self) -> str | None:
        pass
