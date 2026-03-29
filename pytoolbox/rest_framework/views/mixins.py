"""
Mix-ins for building your own Django REST Framework powered API views.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.views import redirect_to_login
from rest_framework import renderers

from pytoolbox import module

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.serializers import Serializer

_all = module.All(globals())


class ActionToQuerysetMixin:
    """Select the queryset based on the current viewset action."""

    querysets = {}

    def get_queryset(self) -> QuerySet:
        """Return the queryset mapped to the current action."""
        return self.querysets.get(self.action, self.queryset)


class ActionToSerializerMixin:
    """Select the serializer class based on the current viewset action."""

    serializers_classes = {}

    def get_serializer_class(self) -> type[Serializer]:
        """Return the serializer class mapped to the current action."""
        return self.serializers_classes.get(self.action, self.serializer_class)


class MethodToQuerysetMixin:
    """Select the queryset based on the HTTP request method."""

    querysets = {}

    def get_queryset(self) -> QuerySet:
        """Return the queryset mapped to the current HTTP method."""
        return self.querysets.get(self.request.method, self.queryset)


class MethodToSerializerMixin:
    """Select the serializer class based on the HTTP request method."""

    serializers_classes = {}

    def get_serializer_class(self) -> type[Serializer]:
        """Return the serializer class mapped to the current HTTP method."""
        return self.serializers_classes.get(self.request.method, self.serializer_class)


class RedirectToLoginMixin:
    """Redirect unauthenticated browsable API requests to the login page."""

    redirected_classes = (renderers.BrowsableAPIRenderer,)

    def finalize_response(
        self,
        request: Request,
        response: Response,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Redirect to login if the user is unauthenticated and using a browser."""
        response = super().finalize_response(request, response, *args, **kwargs)
        logged = request.user.is_authenticated
        if not (logged if isinstance(logged, bool) else logged()) and isinstance(
            response.accepted_renderer, self.redirected_classes
        ):
            response = redirect_to_login(request.path)
            response.data = {}
        return response


__all__ = _all.diff(globals())
