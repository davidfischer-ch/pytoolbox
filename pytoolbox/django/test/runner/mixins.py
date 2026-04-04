"""
Mix-ins for building your own test runners.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import tempfile

from django.conf import settings

__all__ = ['CeleryInMemoryMixin', 'FastPasswordHasherMixin', 'TemporarySendfileRootMixin']


class CeleryInMemoryMixin:
    """Configure Celery to run tasks eagerly in memory during tests."""

    def setup_test_environment(self) -> None:
        """Set Celery to eager in-memory mode."""
        super().setup_test_environment()
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        settings.CELERY_ALWAYS_EAGER = True


class FastPasswordHasherMixin:
    """Use MD5 password hashing during tests for speed."""

    def setup_test_environment(self) -> None:
        """Switch password hasher to MD5 for faster test execution."""
        super().setup_test_environment()
        settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)


class TemporarySendfileRootMixin:
    """Set ``SENDFILE_ROOT`` to a temporary directory during tests."""

    def setup_test_environment(self) -> None:
        """Point ``SENDFILE_ROOT`` to a fresh temporary directory."""
        super().setup_test_environment()
        settings.SENDFILE_ROOT = tempfile.mkdtemp()
