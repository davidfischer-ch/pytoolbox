"""
Extra permission policies for building your own Django REST Framework powered API.
"""

from __future__ import annotations

from typing import override

from oauth2_provider.contrib.rest_framework import OAuth2Authentication, TokenHasReadWriteScope
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

__all__ = ['IsAuthenticatedOrTokenHasReadWriteScope']


class IsAuthenticatedOrTokenHasReadWriteScope(permissions.BasePermission):
    """
    Permission granting a user authenticated other than by OAuth2, or an OAuth2 token holding the
    read or write scope the method needs.
    """

    @override
    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return whether the token has the scope, or the user is authenticated without one."""
        if isinstance(request.successful_authenticator, OAuth2Authentication):
            return TokenHasReadWriteScope().has_permission(request, view)
        return permissions.IsAuthenticated().has_permission(request, view)
