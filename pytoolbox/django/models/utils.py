"""
Some utilities related to the model layer.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox import module

if TYPE_CHECKING:
    from django.db import models

_all = module.All(globals())


def get_base_model(cls_or_instance: type[models.Model] | models.Model) -> type[models.Model]:
    """Return the base (non-proxy) model class for the given class or instance."""
    return cls_or_instance._meta.proxy_for_model or cls_or_instance._meta.model


def get_related_manager(
    cls_or_instance: type[models.Model] | models.Model,
    field: str
) -> models.Manager:
    """Return the default manager for the model related through *field*."""
    return get_related_model(cls_or_instance, field)._default_manager


def get_related_model(
    cls_or_instance: type[models.Model] | models.Model,
    field: str
) -> type[models.Model]:
    """Return the model class related through *field*."""
    if field == 'pk':
        field = cls_or_instance._meta.pk.attname.rstrip('_id')
    return cls_or_instance._meta.get_field(field).related_model


def get_content_type_dict(instance: models.Model) -> dict[str, object]:
    """Return a dictionary with the serialized content type and private key of given instance."""
    from django.contrib.contenttypes import models as ct_models
    content_type = ct_models.ContentType.objects.get_for_model(type(instance))
    return {'app_label': content_type.app_label, 'model': content_type.model, 'pk': instance.pk}


def get_instance(app_label: str, model: str, pk: object) -> models.Model:
    """Return an instance given its app_label, model name and private key."""
    from django.contrib.contenttypes import models as ct_models
    model = ct_models.ContentType.objects.get(app_label=app_label, model=model)
    return model.get_object_for_this_type(pk=pk)


def try_get_field(instance: models.Model, field_name: str) -> object:
    """Return a field value or ``None`` if the related object does not exist."""
    try:
        return getattr(instance, field_name)
    except Exception as ex:
        if type(ex).__name__ != 'RelatedObjectDoesNotExist':
            raise
        return None


__all__ = _all.diff(globals())
