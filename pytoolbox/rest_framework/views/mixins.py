# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.views import redirect_to_login
from rest_framework import renderers

from ... import module

_all = module.All(globals())


class ActionToQuerysetMixin(object):

    querysets = {}

    def get_queryset(self):
        return self.querysets.get(self.action, self.queryset)


class ActionToSerializerMixin(object):

    serializers_classes = {}

    def get_serializer_class(self):
        return self.serializers_classes.get(self.action, self.serializer_class)


class MethodToQuerysetMixin(object):

    querysets = {}

    def get_queryset(self):
        return self.querysets.get(self.request.method, self.queryset)


class MethodToSerializerMixin(object):

    serializers_classes = {}

    def get_serializer_class(self):
        return self.serializers_classes.get(self.request.method, self.serializer_class)


class RedirectToLoginMixin(object):

    redirected_classes = (renderers.BrowsableAPIRenderer, )

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(RedirectToLoginMixin, self).finalize_response(request, response, *args, **kwargs)
        if not request.user.is_authenticated() and isinstance(response.accepted_renderer, self.redirected_classes):
            response = redirect_to_login(request.path)
            response.data = {}
        return response

__all__ = _all.diff(globals())
