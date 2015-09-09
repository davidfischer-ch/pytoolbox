# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#  Origin         : https://github.com/davidfischer-ch/pytoolbox.git
#
#**********************************************************************************************************************#

"""
Permission policies for a Django REST Framework powered API.
"""

from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope
from pytoolbox import module
from rest_framework import permissions

_all = module.All(globals())


class IsAuthenticatedOrTokenHasReadWriteScope(permissions.BasePermission):

    permissions = [permissions.IsAuthenticated(), TokenHasReadWriteScope()]

    def has_permission(self, request, view):
        return any(p.has_permission(request, view) for p in self.permissions)

    def has_object_permission(self, request, view, obj):
        return any(p.has_object_permission(request, view, obj) for p in self.permissions)

__all__ = _all.diff(globals())
