"""
Mix-ins for building your own test runners.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

from django.conf import settings

from pytoolbox.compat import override

if TYPE_CHECKING:
    from django.test.runner import DiscoverRunner

# Each mixin below completes a test runner; naming the base under TYPE_CHECKING states that
# requirement for the checker only.
_RunnerMixin = DiscoverRunner if TYPE_CHECKING else object

__all__ = ['CeleryInMemoryMixin', 'FastPasswordHasherMixin', 'TemporarySendfileRootMixin']


class CeleryInMemoryMixin(_RunnerMixin):
    """Configure Celery to run tasks eagerly in memory during tests."""

    @override
    def setup_test_environment(self, **kwargs: object) -> None:
        """Set Celery to eager in-memory mode."""
        super().setup_test_environment(**kwargs)
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        settings.CELERY_ALWAYS_EAGER = True


class FastPasswordHasherMixin(_RunnerMixin):
    """Use MD5 password hashing during tests for speed."""

    @override
    def setup_test_environment(self, **kwargs: object) -> None:
        """Switch password hasher to MD5 for faster test execution."""
        super().setup_test_environment(**kwargs)
        settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)


class TemporarySendfileRootMixin(_RunnerMixin):
    """Set ``SENDFILE_ROOT`` to a temporary directory during tests."""

    @override
    def setup_test_environment(self, **kwargs: object) -> None:
        """Point ``SENDFILE_ROOT`` to a fresh temporary directory."""
        super().setup_test_environment(**kwargs)
        settings.SENDFILE_ROOT = tempfile.mkdtemp()
