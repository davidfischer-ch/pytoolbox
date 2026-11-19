"""
Extra `fields <http://www.django-rest-framework.org/api-guide/fields/>`_ for building your own
`Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_ powered API
`serializers <http://www.django-rest-framework.org/tutorial/1-serialization/>`_.
"""

from __future__ import annotations

import warnings
from typing import Any

from rest_framework import serializers

__all__ = ['StripCharField']


class StripCharField(serializers.CharField):
    """
    A :class:`~rest_framework.serializers.CharField`, which strips whitespace and rejects a blank
    value.

    .. deprecated:: 14.13.0
       Use :class:`~rest_framework.serializers.CharField` instead, which does both by default.
    """

    def __init__(self, **kwargs: Any) -> None:
        warnings.warn(
            'StripCharField is deprecated; use rest_framework.serializers.CharField.',
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)
