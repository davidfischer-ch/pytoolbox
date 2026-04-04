"""
Mix-ins for building your own
`Django REST Framework <https://github.com/encode/django-rest-framework>`_ powered API
`metadata <https://github.com/encode/django-rest-framework/blob/master/rest_framework/metadata.py>`_
.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from rest_framework import serializers

__all__ = ['ExcludeRelatedChoicesMixin']


class ExcludeRelatedChoicesMixin:
    """Do not includes related fields to avoid having choices with hundreds instances."""

    related_fields = (serializers.RelatedField, serializers.ManyRelatedField)

    def get_field_info(self, field: serializers.Field) -> OrderedDict[str, Any]:
        """Return field info, stripping choices from related fields."""
        if hasattr(field, 'choices') and isinstance(field, self.related_fields):
            field_class = type(field)

            class HaveNoChoicesProxy(field_class):
                """Proxy that hides the choices property from related fields."""

                @property
                def choices(self) -> None:
                    """Raise AttributeError to hide choices from metadata."""
                    raise AttributeError

            try:
                field.__class__ = HaveNoChoicesProxy
                return super().get_field_info(field)
            finally:
                field.__class__ = field_class
        return super().get_field_info(field)
