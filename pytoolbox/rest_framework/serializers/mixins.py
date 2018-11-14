# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own `Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_
powered API `serializers <http://www.django-rest-framework.org/tutorial/1-serialization/>`_.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from pytoolbox import module
from pytoolbox.django.models import utils

_all = module.All(globals())


class BaseModelMixin(object):

    def build_url_field(self, field_name, model_class):
        return super(BaseModelMixin, self).build_url_field(
            field_name, utils.get_base_model(model_class))


class FromPrivateKeyMixin(object):
    """
    Allow to provide the PK of the model to retrieve it instead of creating a new instance with
    fields from data.
    """

    default_error_messages = {
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def to_internal_value(self, data):
        """Transform the *incoming* primitive data into a native value."""
        if not data or isinstance(data, dict):
            return super(FromPrivateKeyMixin, self).to_internal_value(data)
        try:
            return self.Meta.model.objects.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def create(self, validated_data):
        if isinstance(validated_data, self.Meta.model):
            return validated_data
        return super(FromPrivateKeyMixin, self).create(validated_data)


class NestedWriteMixin(object):

    def to_internal_value(self, data):
        """
        Return a tuple with (self, validate_data) to allow working on validated data with this
        serializer.
        """
        return self, super(NestedWriteMixin, self).to_internal_value(data)


class ReadOnlyMixin(object):

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(ReadOnlyMixin, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        raise AttributeError('Read-only serializer')

    def update(self, task, validated_data):
        raise AttributeError('Read-only serializer')


__all__ = _all.diff(globals())
