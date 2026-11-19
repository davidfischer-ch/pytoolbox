"""Tests for the rest_framework.views.mixins module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock

from django.contrib.auth.models import User
from rest_framework import viewsets

from pytoolbox.rest_framework.views import mixins


def test_action_to_queryset_mixin_matched() -> None:
    """The action's queryset is returned as a fresh clone, never the shared class attribute."""

    class UserViewSet(mixins.ActionToQuerysetMixin, viewsets.GenericViewSet):
        """Viewset listing the staff."""

        queryset = User.objects.all()
        querysets = {'list': User.objects.filter(is_staff=True)}

    view = UserViewSet(action='list')
    queryset = view.get_queryset()
    assert queryset is not UserViewSet.querysets['list']
    assert str(queryset.query) == str(UserViewSet.querysets['list'].query)


def test_action_to_queryset_mixin_fallback() -> None:
    """An unmapped action gets the view's queryset as a fresh clone, as DRF's get_queryset does."""

    class UserViewSet(mixins.ActionToQuerysetMixin, viewsets.GenericViewSet):
        """Viewset listing the staff."""

        queryset = User.objects.all()
        querysets = {'list': User.objects.filter(is_staff=True)}

    view = UserViewSet(action='retrieve', queryset=User.objects.filter(is_active=True))
    queryset = view.get_queryset()
    assert queryset is not view.queryset
    assert str(queryset.query) == str(User.objects.filter(is_active=True).query)


def test_action_to_serializer_mixin_matched() -> None:
    """Returns the action-specific serializer class when the action matches."""

    class FakeView(mixins.ActionToSerializerMixin):
        """Fake view with action-specific serializers."""

        serializer_class = 'DefaultSerializer'
        serializers_classes = {'list': 'ListSerializer'}
        action = 'list'

    view = FakeView()
    assert view.get_serializer_class() == 'ListSerializer'


def test_action_to_serializer_mixin_fallback() -> None:
    """Falls back to the default serializer class for unmapped actions."""

    class FakeView(mixins.ActionToSerializerMixin):
        """Fake view with action-specific serializers."""

        serializer_class = 'DefaultSerializer'
        serializers_classes = {'list': 'ListSerializer'}
        action = 'create'

    view = FakeView()
    assert view.get_serializer_class() == 'DefaultSerializer'


def test_method_to_queryset_mixin_matched() -> None:
    """The method's queryset is returned as a fresh clone, never the shared class attribute."""

    class UserViewSet(mixins.MethodToQuerysetMixin, viewsets.GenericViewSet):
        """Viewset listing the staff."""

        queryset = User.objects.all()
        querysets = {'GET': User.objects.filter(is_staff=True)}

    view = UserViewSet(request=MagicMock(method='GET'))
    queryset = view.get_queryset()
    assert queryset is not UserViewSet.querysets['GET']
    assert str(queryset.query) == str(UserViewSet.querysets['GET'].query)


def test_method_to_queryset_mixin_fallback() -> None:
    """An unmapped method gets the view's queryset as a fresh clone, as DRF's get_queryset does."""

    class UserViewSet(mixins.MethodToQuerysetMixin, viewsets.GenericViewSet):
        """Viewset listing the staff."""

        queryset = User.objects.all()
        querysets = {'GET': User.objects.filter(is_staff=True)}

    view = UserViewSet(
        queryset=User.objects.filter(is_active=True), request=MagicMock(method='POST')
    )
    queryset = view.get_queryset()
    assert queryset is not view.queryset
    assert str(queryset.query) == str(User.objects.filter(is_active=True).query)


def test_method_to_serializer_mixin_matched() -> None:
    """Returns the method-specific serializer class when the HTTP method matches."""

    class FakeView(mixins.MethodToSerializerMixin):
        """Fake view with method-specific serializers."""

        serializer_class = 'DefaultSerializer'
        serializers_classes = {'POST': 'PostSerializer'}
        request = MagicMock(method='POST')

    view = FakeView()
    assert view.get_serializer_class() == 'PostSerializer'


def test_method_to_serializer_mixin_fallback() -> None:
    """Falls back to the default serializer class for unmapped HTTP methods."""

    class FakeView(mixins.MethodToSerializerMixin):
        """Fake view with method-specific serializers."""

        serializer_class = 'DefaultSerializer'
        serializers_classes = {'POST': 'PostSerializer'}
        request = MagicMock(method='GET')

    view = FakeView()
    assert view.get_serializer_class() == 'DefaultSerializer'


def test_redirect_to_login_mixin_authenticated() -> None:
    """Authenticated users get the original response, no redirect."""

    class Base:
        """Base class providing finalize_response."""

        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            """Finalize response implementation."""
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        """Fake view combining RedirectToLoginMixin with base."""

    view = FakeView()
    request = MagicMock()
    request.user.is_authenticated = True
    response = MagicMock()
    response.accepted_renderer = MagicMock()

    result = view.finalize_response(request, response)
    assert result is response


def test_redirect_to_login_mixin_unauthenticated_non_browsable() -> None:
    """Unauthenticated users with non-browsable renderers get no redirect."""

    class Base:
        """Base class providing finalize_response."""

        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            """Finalize response implementation."""
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        """Fake view combining RedirectToLoginMixin with base."""

    view = FakeView()
    request = MagicMock()
    request.user.is_authenticated = False
    response = MagicMock()
    response.accepted_renderer = MagicMock()  # Not a BrowsableAPIRenderer

    result = view.finalize_response(request, response)
    assert result is response


def test_redirect_to_login_mixin_unauthenticated_browsable() -> None:
    """Unauthenticated users with BrowsableAPIRenderer are redirected to login."""
    from unittest.mock import patch

    from rest_framework import renderers

    class Base:
        """Base class providing finalize_response."""

        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            """Finalize response implementation."""
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        """Fake view combining RedirectToLoginMixin with base."""

    view = FakeView()
    request = MagicMock()
    request.user.is_authenticated = False
    request.path = '/api/items/'
    response = MagicMock()
    response.accepted_renderer = renderers.BrowsableAPIRenderer()

    redirect_response = MagicMock()
    with patch(
        'pytoolbox.rest_framework.views.mixins.redirect_to_login',
        return_value=redirect_response,
    ) as mock_redirect:
        result = view.finalize_response(request, response)
        mock_redirect.assert_called_once_with('/api/items/')
        assert result is redirect_response
        assert result.data == {}
