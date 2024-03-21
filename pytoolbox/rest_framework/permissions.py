"""
Extra permission policies for building your own Django REST Framework powered API.
"""
from __future__ import annotations

from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope
from rest_framework import permissions

__all__ = ['IsAuthenticatedOrTokenHasReadWriteScope']


class IsAuthenticatedOrTokenHasReadWriteScope(permissions.BasePermission):

    permissions = [permissions.IsAuthenticated(), TokenHasReadWriteScope()]

    def has_permission(self, request, view):
        return any(p.has_permission(request, view) for p in self.permissions)

    def has_object_permission(self, request, view, obj):
        return any(p.has_object_permission(request, view, obj) for p in self.permissions)
