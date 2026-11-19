"""Tests for the rest_framework.permissions module."""

from __future__ import annotations

from unittest import mock

from django.http.request import HttpHeaders
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


def test_has_permission_refuses_a_token_without_the_scope_relayed_by_the_session() -> None:
    """A bearer token the middleware authenticated is held to its scope, relayed as a session."""
    request = _request('GET', SessionAuthentication(), bearer_token='token')
    assert IsAuthenticatedOrTokenHasReadWriteScope().has_permission(request, _view()) is False


def test_has_permission_grants_a_user_of_another_bearer_scheme() -> None:
    """A user another bearer scheme authenticated, a JWT for one, is granted access."""
    request = _request('GET', SessionAuthentication(), bearer_token='jwt', backend=None)
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
    backend: str | None = 'oauth2_provider.backends.OAuth2Backend',
    bearer_token: str | None = None,
    token_valid: bool | None = None,
) -> mock.Mock:
    """
    Return a request authenticated by *authenticator*, with a token when *token_valid* is set.

    A *bearer_token* shapes the request as OAuth2TokenMiddleware leaves it: the header kept, the
    user set by *backend*, and no token for the authenticator relaying that user.
    """
    token = None
    if token_valid is not None:
        token = mock.Mock(spec=['allow_scopes', 'is_expired', 'is_valid', 'scope'])
        token.is_valid.return_value = token_valid
    user = mock.Mock(spec=['is_authenticated'], is_authenticated=authenticated)
    meta: dict[str, str] = {}
    if bearer_token is not None:
        meta['HTTP_AUTHORIZATION'] = f'Bearer {bearer_token}'
        if backend is not None:
            user.backend = backend
    return mock.Mock(
        META=meta,
        auth=token,
        headers=HttpHeaders(meta),
        method=method,
        successful_authenticator=authenticator,
        user=user,
    )


def _view() -> mock.Mock:
    """Return a view declaring no required scope."""
    return mock.Mock(spec=[])
