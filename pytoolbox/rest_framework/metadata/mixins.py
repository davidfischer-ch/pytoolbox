"""
Mix-ins for building your own
`Django REST Framework <https://github.com/encode/django-rest-framework>`_ powered API
`metadata <https://github.com/encode/django-rest-framework/blob/master/rest_framework/metadata.py>`_
.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import serializers

from pytoolbox.compat import override

__all__ = ['ExcludeRelatedChoicesMixin']


if TYPE_CHECKING:
    from rest_framework.metadata import SimpleMetadata

# The mixins complete DRF's SimpleMetadata; naming the base under TYPE_CHECKING states that
# requirement for the checker only.
_MetadataMixin = SimpleMetadata if TYPE_CHECKING else object


class ExcludeRelatedChoicesMixin(_MetadataMixin):
    """Do not includes related fields to avoid having choices with hundreds instances."""

    related_fields = (serializers.RelatedField, serializers.ManyRelatedField)

    @override
    def get_field_info(self, field: serializers.Field) -> dict[str, Any]:
        """Return field info, stripping choices from related fields."""
        if hasattr(field, 'choices') and isinstance(field, self.related_fields):
            field_class: type[serializers.Field] = type(field)

            class HaveNoChoicesProxy(field_class):  # type: ignore[valid-type,misc]
                """Proxy that hides the choices property from related fields."""

                @property
                def choices(self) -> None:
                    """Raise AttributeError to hide choices from metadata."""
                    raise AttributeError

            try:
                # Swapping __class__ in and out is what hides `choices` for one call; no checker can
                # follow a class built from a variable.
                field.__class__ = HaveNoChoicesProxy  # pyrefly: ignore[bad-argument-type]
                return super().get_field_info(field)
            finally:
                field.__class__ = field_class  # pyrefly: ignore[bad-argument-type]
        return super().get_field_info(field)
