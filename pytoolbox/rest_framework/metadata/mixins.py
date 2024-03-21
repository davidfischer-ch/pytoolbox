"""
Mix-ins for building your own
`Django REST Framework <https://github.com/encode/django-rest-framework>`_ powered API
`metadata <https://github.com/encode/django-rest-framework/blob/master/rest_framework/metadata.py>`_
.
"""
from __future__ import annotations

from rest_framework import serializers

__all__ = ['ExcludeRelatedChoicesMixin']


class ExcludeRelatedChoicesMixin(object):
    """Do not includes related fields to avoid having choices with hundreds instances."""

    related_fields = (serializers.RelatedField, serializers.ManyRelatedField)

    def get_field_info(self, field):
        if hasattr(field, 'choices') and isinstance(field, self.related_fields):
            field_class = field.__class__

            class HaveNoChoicesProxy(field_class):

                @property
                def choices(self):
                    raise AttributeError

            try:
                field.__class__ = HaveNoChoicesProxy
                return super().get_field_info(field)
            finally:
                field.__class__ = field_class
        return super().get_field_info(field)
