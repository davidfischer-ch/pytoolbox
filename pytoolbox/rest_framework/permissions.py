# -*- encoding: utf-8 -*-

"""
Extra `permission policies <http://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/>`_
for building your own `Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_
powered API.
"""

from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope
from rest_framework import permissions

from pytoolbox import module

_all = module.All(globals())


class IsAuthenticatedOrTokenHasReadWriteScope(permissions.BasePermission):

    permissions = [permissions.IsAuthenticated(), TokenHasReadWriteScope()]

    def has_permission(self, request, view):
        return any(p.has_permission(request, view) for p in self.permissions)

    def has_object_permission(self, request, view, obj):
        return any(p.has_object_permission(request, view, obj) for p in self.permissions)


__all__ = _all.diff(globals())
