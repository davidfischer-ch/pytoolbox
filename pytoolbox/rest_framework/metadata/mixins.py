"""
Mix-ins for building your own
`Django REST Framework <https://github.com/encode/django-rest-framework>`_ powered API
`metadata <https://github.com/encode/django-rest-framework/blob/master/rest_framework/metadata.py>`_
.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rest_framework.metadata import SimpleMetadata

__all__ = ['ExcludeRelatedChoicesMixin']

# The mixins complete DRF's SimpleMetadata; naming the base under TYPE_CHECKING states that
# requirement for the checker only.
_MetadataMixin = SimpleMetadata if TYPE_CHECKING else object


class ExcludeRelatedChoicesMixin(_MetadataMixin):
    """
    Empty mix-in: :class:`~rest_framework.metadata.SimpleMetadata` omits the choices of related
    fields, which may list hundreds of instances.

    .. deprecated:: 14.13.0
       Use :class:`~rest_framework.metadata.SimpleMetadata` instead.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            'ExcludeRelatedChoicesMixin is deprecated; use rest_framework.metadata.SimpleMetadata.',
            DeprecationWarning,
            stacklevel=2,
        )
