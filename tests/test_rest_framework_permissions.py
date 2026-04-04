from __future__ import annotations

import sys
from unittest import mock

# Inject mocks for oauth2_provider.ext.rest_framework before importing permissions module
sys.modules.setdefault('oauth2_provider.ext', mock.MagicMock())
sys.modules.setdefault('oauth2_provider.ext.rest_framework', mock.MagicMock())

# must follow sys.modules patching above
# pylint: disable=wrong-import-position
from pytoolbox.rest_framework.permissions import (  # noqa: E402
    IsAuthenticatedOrTokenHasReadWriteScope,
)


def test_has_permission_true_when_first_sub_permission_allows(request_mock, view_mock) -> None:
    """HasPermission returns True if any sub-permission allows access."""
    perm = IsAuthenticatedOrTokenHasReadWriteScope()
    p1, p2 = mock.MagicMock(), mock.MagicMock()
    p1.has_permission.return_value = True
    perm.permissions = [p1, p2]
    assert perm.has_permission(request_mock, view_mock) is True
    p1.has_permission.assert_called_once_with(request_mock, view_mock)
    p2.has_permission.assert_not_called()  # short-circuited


def test_has_permission_true_when_only_second_sub_permission_allows(
    request_mock,
    view_mock,
) -> None:
    """Has permission returns True if any sub-permission allows (not just the first)."""
    perm = IsAuthenticatedOrTokenHasReadWriteScope()
    p1, p2 = mock.MagicMock(), mock.MagicMock()
    p1.has_permission.return_value = False
    p2.has_permission.return_value = True
    perm.permissions = [p1, p2]
    assert perm.has_permission(request_mock, view_mock) is True


def test_has_permission_false_when_no_sub_permission_allows(request_mock, view_mock) -> None:
    """HasPermission returns False when no sub-permission allows access."""
    perm = IsAuthenticatedOrTokenHasReadWriteScope()
    p1, p2 = mock.MagicMock(), mock.MagicMock()
    p1.has_permission.return_value = False
    p2.has_permission.return_value = False
    perm.permissions = [p1, p2]
    assert perm.has_permission(request_mock, view_mock) is False
