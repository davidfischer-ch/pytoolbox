"""
Extra permission policies for building your own Django REST Framework powered API.
"""

from __future__ import annotations

from typing import override

from django.utils.module_loading import import_string
from oauth2_provider.backends import OAuth2Backend
from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasReadWriteScope
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

__all__ = ['IsAuthenticatedOrTokenHasReadWriteScope']


class IsAuthenticatedOrTokenHasReadWriteScope(permissions.BasePermission):
    """
    Permission granting a user authenticated other than by OAuth2, or an OAuth2 token holding the
    read or write scope the method needs.

    A user an OAuth2 access token authenticated is held to the scope whichever authenticator relayed
    it, such as :class:`~rest_framework.authentication.SessionAuthentication` after
    ``OAuth2TokenMiddleware``: it is refused unless ``OAuth2Authentication`` gave its token. A user
    of another bearer scheme, a JWT for one, needs only to be authenticated.
    """

    @override
    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return whether the token has the scope, or the user is authenticated without one."""
        if _is_token_authenticated(request):
            return TokenHasReadWriteScope().has_permission(request, view)
        return permissions.IsAuthenticated().has_permission(request, view)


# --- Internals ------------------------------------------------------------------------------------


def _is_token_authenticated(request: Request) -> bool:
    """Return whether an OAuth2 access token authenticated *request*, through any authenticator."""
    if isinstance(request.successful_authenticator, OAuth2Authentication):
        return True
    backend = getattr(request.user, 'backend', None)
    return isinstance(backend, str) and issubclass(import_string(backend), OAuth2Backend)
