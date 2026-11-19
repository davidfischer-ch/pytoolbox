"""
Mix-ins for building your own
`Django REST Framework <https://github.com/encode/django-rest-framework>`_ powered API
`metadata <https://github.com/encode/django-rest-framework/blob/master/rest_framework/metadata.py>`_
.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, ClassVar, override

from rest_framework import serializers

if TYPE_CHECKING:
    from rest_framework.metadata import SimpleMetadata

__all__ = ['ExcludeRelatedChoicesMixin']

# The mixins complete DRF's SimpleMetadata; naming the base under TYPE_CHECKING states that
# requirement for the checker only.
_MetadataMixin = SimpleMetadata if TYPE_CHECKING else object


class ExcludeRelatedChoicesMixin(_MetadataMixin):
    """
    Mix-in omitting the choices of the fields of the classes in ``related_fields``, which may list
    hundreds of instances. :class:`~rest_framework.metadata.SimpleMetadata` omits those of its
    related fields alone, the default of ``related_fields``.

    .. deprecated:: 14.13.0
       Use :class:`~rest_framework.metadata.SimpleMetadata` instead.
    """

    related_fields: ClassVar[tuple[type[serializers.Field], ...]] = (
        serializers.RelatedField,
        serializers.ManyRelatedField,
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            'ExcludeRelatedChoicesMixin is deprecated; use rest_framework.metadata.SimpleMetadata.',
            DeprecationWarning,
            stacklevel=2,
        )

    @override
    def get_field_info(self, field: serializers.Field) -> dict[str, Any]:
        """Return the information of *field*, without choices for a class in ``related_fields``."""
        field_info = super().get_field_info(field)
        if isinstance(field, self.related_fields):
            field_info.pop('choices', None)
        return field_info
