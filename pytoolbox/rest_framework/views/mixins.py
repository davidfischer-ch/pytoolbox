"""
Mix-ins for building your own Django REST Framework powered API views.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.views import redirect_to_login
from rest_framework import renderers

from pytoolbox import module
from pytoolbox.compat import override

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework import viewsets
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.serializers import Serializer

# Each mixin below completes a DRF generic view and reads its attributes (`action`, `request`,
# `get_queryset`, ...); naming the base under TYPE_CHECKING states that for the checker only.
_ViewsMixin = viewsets.GenericViewSet if TYPE_CHECKING else object

_all = module.All(globals())


class ActionToQuerysetMixin(_ViewsMixin):
    """Select the queryset based on the current viewset action."""

    querysets = {}

    @override
    def get_queryset(self) -> QuerySet:
        """Return the queryset mapped to the current action."""
        return self.querysets.get(self.action, self.queryset)


class ActionToSerializerMixin(_ViewsMixin):
    """Select the serializer class based on the current viewset action."""

    serializers_classes = {}

    @override
    def get_serializer_class(self) -> type[Serializer]:
        """Return the serializer class mapped to the current action."""
        return self.serializers_classes.get(self.action, self.serializer_class)


class MethodToQuerysetMixin(_ViewsMixin):
    """Select the queryset based on the HTTP request method."""

    querysets = {}

    @override
    def get_queryset(self) -> QuerySet:
        """Return the queryset mapped to the current HTTP method."""
        return self.querysets.get(self.request.method, self.queryset)


class MethodToSerializerMixin(_ViewsMixin):
    """Select the serializer class based on the HTTP request method."""

    serializers_classes = {}

    @override
    def get_serializer_class(self) -> type[Serializer]:
        """Return the serializer class mapped to the current HTTP method."""
        return self.serializers_classes.get(self.request.method, self.serializer_class)


class RedirectToLoginMixin(_ViewsMixin):
    """Redirect unauthenticated browsable API requests to the login page."""

    redirected_classes = (renderers.BrowsableAPIRenderer,)

    @override
    def finalize_response(
        self,
        request: Request,
        response: Response,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Redirect to login if the user is unauthenticated and using a browser."""
        api_response = super().finalize_response(request, response, *args, **kwargs)
        logged = request.user.is_authenticated
        if not (logged if isinstance(logged, bool) else logged()) and isinstance(
            api_response.accepted_renderer, self.redirected_classes
        ):
            redirection = redirect_to_login(request.path)
            redirection.data = {}  # type: ignore[attr-defined]
            return redirection  # pyrefly: ignore[bad-return]
        return api_response


__all__ = _all.diff(globals())
