"""Tests for the rest_framework.permissions module."""

from __future__ import annotations

from unittest import mock

from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.authentication import SessionAuthentication

from pytoolbox.rest_framework.permissions import IsAuthenticatedOrTokenHasReadWriteScope


def test_has_permission_refuses_a_token_without_the_scope() -> None:
    """An OAuth2 token lacking the write scope is refused a write, its user authenticated."""
    request = _request('POST', OAuth2Authentication(), token_valid=False)
    assert IsAuthenticatedOrTokenHasReadWriteScope().has_permission(request, _view()) is False


def test_has_permission_grants_a_token_with_the_scope() -> None:
    """An OAuth2 token holding the scope the method needs is granted access."""
    request = _request('GET', OAuth2Authentication(), token_valid=True)
    assert IsAuthenticatedOrTokenHasReadWriteScope().has_permission(request, _view()) is True


def test_has_permission_grants_a_user_authenticated_otherwise() -> None:
    """A user authenticated other than by OAuth2 is granted access, with no token."""
    request = _request('POST', SessionAuthentication())
    assert IsAuthenticatedOrTokenHasReadWriteScope().has_permission(request, _view()) is True


def test_has_permission_refuses_an_anonymous_user() -> None:
    """An anonymous request is refused."""
    request = _request('GET', None, authenticated=False)
    assert IsAuthenticatedOrTokenHasReadWriteScope().has_permission(request, _view()) is False


# --- Internals ------------------------------------------------------------------------------------


def _request(
    method: str,
    authenticator: object,
    *,
    authenticated: bool = True,
    token_valid: bool | None = None,
) -> mock.Mock:
    """Return a request authenticated by *authenticator*, with a token when *token_valid* is set."""
    token = None
    if token_valid is not None:
        token = mock.Mock(spec=['allow_scopes', 'is_expired', 'is_valid', 'scope'])
        token.is_valid.return_value = token_valid
    return mock.Mock(
        auth=token,
        method=method,
        successful_authenticator=authenticator,
        user=mock.Mock(is_authenticated=authenticated),
    )


def _view() -> mock.Mock:
    """Return a view declaring no required scope."""
    return mock.Mock(spec=[])
