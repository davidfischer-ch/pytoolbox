from pytoolbox import decorators
from . import brand, equipment  # pylint:disable=unused-import

__all__ = ['Lens']


class Lens(equipment.Equipement):

    brand_class = brand.Brand

    @property
    def brand(self):
        brands = {t.brand for t in self.tags.values() if t.brand}
        if brands:
            assert len(brands) == 1, brands
            return next(iter(brands))
        # Extract brand from model
        return self.brand_class(self._model.split(' ')[0])

    @property
    def _model(self):
        return next((t.data for t in self.tags.values() if 'model' in t.label.lower()), None)

    @decorators.cached_property
    def tags(self):
        return {k: t for k, t in self.metadata.tags.items() if 'lens' in t.label.lower()}
