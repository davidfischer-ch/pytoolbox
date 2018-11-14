# -*- encoding: utf-8 -*-

"""
Extra `fields <http://www.django-rest-framework.org/api-guide/fields/>`_ for building your own
`Django REST Framework <https://github.com/tomchristie/django-rest-framework>`_ powered API
`serializers <http://www.django-rest-framework.org/tutorial/1-serialization/>`_.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from rest_framework import serializers

from pytoolbox import module
from pytoolbox.django.core.validators import EmptyValidator

_all = module.All(globals())


class StripCharField(serializers.CharField):

    def __init__(self, **kwargs):
        super(StripCharField, self).__init__(**kwargs)
        self.validators.append(EmptyValidator(message=self.error_messages['blank']))

    def to_internal_value(self, data):
        data = super(StripCharField, self).to_internal_value(data)
        return data.strip() if data else data


__all__ = _all.diff(globals())
