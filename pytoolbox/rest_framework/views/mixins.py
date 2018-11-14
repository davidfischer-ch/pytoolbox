# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own `Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_
powered API `views <http://www.django-rest-framework.org/tutorial/3-class-based-views/>`_.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth.views import redirect_to_login
from rest_framework import renderers

from pytoolbox import module

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
        response = super(RedirectToLoginMixin, self).finalize_response(
            request, response, *args, **kwargs)
        if (
            not request.user.is_authenticated() and
            isinstance(response.accepted_renderer, self.redirected_classes)
        ):
            response = redirect_to_login(request.path)
            response.data = {}
        return response


__all__ = _all.diff(globals())
