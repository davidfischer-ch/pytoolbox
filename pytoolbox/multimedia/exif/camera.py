from pytoolbox import decorators
from . import brand, equipment  # pylint:disable=unused-import

__all__ = ['Camera']


class Camera(equipment.Equipement):

    brand_class = brand.Brand

    @property
    def brand(self):
        return self.brand_class(self.metadata['Exif.Image.Make'].data)

    @property
    def _model(self):
        return self.metadata['Exif.Image.Model'].data

    @decorators.cached_property
    def tags(self):
        return {k: t for k, t in self.metadata.tags.items() if 'camera' in t.label.lower()}
