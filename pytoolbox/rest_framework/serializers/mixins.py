"""
Mix-ins for building your own Django REST Framework powered API serializers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _

from pytoolbox.django.models import utils

if TYPE_CHECKING:
    from django.db import models
    from rest_framework.serializers import Serializer

__all__ = ['BaseModelMixin', 'FromPrivateKeyMixin', 'NestedWriteMixin', 'ReadOnlyMixin']


class BaseModelMixin:
    """Build URL fields using the base (non-proxy) model class."""

    def build_url_field(self, field_name: str, model_class: type[models.Model]) -> Any:
        """Return a URL field resolved against the base model."""
        return super().build_url_field(field_name, utils.get_base_model(model_class))


class FromPrivateKeyMixin:
    """
    Allow to provide the PK of the model to retrieve it instead of creating a new instance with
    fields from data.
    """

    default_error_messages = {
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def to_internal_value(self, data: Any) -> Any:
        """Transform the *incoming* primitive data into a native value."""
        if not data or isinstance(data, dict):
            return super().to_internal_value(data)
        try:
            return self.Meta.model.objects.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=smart_str(data))
            return None  # self.fail() always raises
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)
            return None  # self.fail() always raises

    def create(self, validated_data: Any) -> Any:
        """Return the instance directly if already resolved, otherwise create it."""
        if isinstance(validated_data, self.Meta.model):
            return validated_data
        return super().create(validated_data)


class NestedWriteMixin:
    """Return ``(serializer, validated_data)`` tuples for nested writes."""

    def to_internal_value(self, data: Any) -> tuple[Serializer, Any]:
        """
        Return a tuple with (self, validate_data) to allow working on validated data with this
        serializer.
        """
        return self, super().to_internal_value(data)


class ReadOnlyMixin:
    """Force the serializer into read-only mode, rejecting create and update."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs['read_only'] = True
        super().__init__(*args, **kwargs)

    def create(self, validated_data: Any) -> NoReturn:
        """Raise :class:`AttributeError` unconditionally."""
        raise AttributeError('Read-only serializer')

    def update(self, task: Any, validated_data: Any) -> NoReturn:
        """Raise :class:`AttributeError` unconditionally."""
        raise AttributeError('Read-only serializer')
