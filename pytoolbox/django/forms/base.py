"""
Extra forms.
"""
from __future__ import annotations

from django.utils.functional import cached_property

from pytoolbox.django.models import utils

__all__ = ['SerializedInstanceForm']


class SerializedInstanceForm(object):
    """Form that serializes and deserializes a model instance by content type."""

    def __init__(self, **kwargs):
        self.app_label = kwargs['app_label']
        self.model = kwargs['model']
        self.pk = kwargs['pk']

    @classmethod
    def serialize(cls, instance):
        """Return a content-type dictionary for the given model instance."""
        return utils.get_content_type_dict(instance)

    @cached_property
    def instance(self):
        """Return the deserialized model instance from the database."""
        return utils.get_instance(self.app_label, self.model, self.pk)

    def is_valid(self):
        """Return ``True`` if the serialized instance exists in the database."""
        try:
            return bool(self.instance)
        except Exception:
            return False
