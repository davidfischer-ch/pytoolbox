"""
Extra `fields <http://www.django-rest-framework.org/api-guide/fields/>`_ for building your own
`Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_ powered API
`serializers <http://www.django-rest-framework.org/tutorial/1-serialization/>`_.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from pytoolbox.django.core.validators import EmptyValidator

__all__ = ['StripCharField']


class StripCharField(serializers.CharField):
    """A :class:`~rest_framework.serializers.CharField` that strips whitespace."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.validators.append(EmptyValidator(message=self.error_messages['blank']))

    def to_internal_value(self, data: Any) -> str:
        """Return the stripped value of the incoming data."""
        data = super().to_internal_value(data)
        return data.strip() if data else data
