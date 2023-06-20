from __future__ import annotations

from pytoolbox import decorators

from .brand import Brand
from .equipment import Equipement

__all__ = ['Lens']


class Lens(Equipement):

    brand_class = Brand

    @property
    def brand(self) -> Brand | None:
        if brands := {t.brand for t in self.tags.values() if t.brand}:
            assert len(brands) == 1, brands
            return next(iter(brands))
        # Extract brand from model
        model = self._model
        return self.brand_class(model.split(' ')[0]) if model else None

    @property
    def _model(self) -> str | None:
        return next((t.data for t in self.tags.values() if 'model' in t.label.lower()), None)

    @decorators.cached_property
    def tags(self) -> dict:  # type: ignore[override]  # pylint: disable=invalid-overridden-method
        return {k: t for k, t in self.metadata.tags.items() if 'lens' in t.label.lower()}
