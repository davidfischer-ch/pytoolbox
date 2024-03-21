"""
Mix-ins for building your own test runners.
"""
from __future__ import annotations

import tempfile

from django.conf import settings

__all__ = ['CeleryInMemoryMixin', 'FastPasswordHasherMixin', 'TemporarySendfileRootMixin']


class CeleryInMemoryMixin(object):

    def setup_test_environment(self):
        super().setup_test_environment()
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        settings.CELERY_ALWAYS_EAGER = True


class FastPasswordHasherMixin(object):

    def setup_test_environment(self):
        super().setup_test_environment()
        settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher', )


class TemporarySendfileRootMixin(object):

    def setup_test_environment(self):
        super().setup_test_environment()
        settings.SENDFILE_ROOT = tempfile.mkdtemp()
