# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own test runners.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import tempfile

from django.conf import settings

from pytoolbox import module

_all = module.All(globals())


class CeleryInMemoryMixin(object):

    def setup_test_environment(self):
        super(CeleryInMemoryMixin, self).setup_test_environment()
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        settings.CELERY_ALWAYS_EAGER = True


class FastPasswordHasherMixin(object):

    def setup_test_environment(self):
        super(FastPasswordHasherMixin, self).setup_test_environment()
        settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher', )


class TemporarySendfileRootMixin(object):

    def setup_test_environment(self):
        super(TemporarySendfileRootMixin, self).setup_test_environment()
        settings.SENDFILE_ROOT = tempfile.mkdtemp()


__all__ = _all.diff(globals())
