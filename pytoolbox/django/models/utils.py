# -*- encoding: utf-8 -*-

"""
Some utilities related to the model layer.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

_all = module.All(globals())


def get_base_model(cls_or_instance):
    return cls_or_instance._meta.proxy_for_model or cls_or_instance._meta.model


def get_related_manager(cls_or_instance, field):
    return get_related_model(cls_or_instance, field)._default_manager


def get_related_model(cls_or_instance, field):
    if field == 'pk':
        field = cls_or_instance._meta.pk.attname.rstrip('_id')
    return cls_or_instance._meta.get_field(field).related_model


def get_content_type_dict(instance):
    """Return a dictionary with the serialized content type and private key of given instance."""
    from django.contrib.contenttypes import models as ct_models
    content_type = ct_models.ContentType.objects.get_for_model(instance.__class__)
    return {'app_label': content_type.app_label, 'model': content_type.model, 'pk': instance.pk}


def get_instance(app_label, model, pk):
    """Return an instance given its app_label, model name and private key."""
    from django.contrib.contenttypes import models as ct_models
    model = ct_models.ContentType.objects.get(app_label=app_label, model=model)
    return model.get_object_for_this_type(pk=pk)


def try_get_field(instance, field_name):
    try:
        return getattr(instance, field_name)
    except Exception as e:
        if e.__class__.__name__ != 'RelatedObjectDoesNotExist':
            raise


__all__ = _all.diff(globals())
