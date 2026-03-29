from __future__ import annotations

from unittest.mock import MagicMock

from pytoolbox.rest_framework.views import mixins


def test_action_to_queryset_mixin_matched() -> None:
    """Returns the action-specific queryset when the action matches."""

    class FakeView(mixins.ActionToQuerysetMixin):
        queryset = 'default_qs'
        querysets = {'list': 'list_qs', 'create': 'create_qs'}
        action = 'list'

    view = FakeView()
    assert view.get_queryset() == 'list_qs'


def test_action_to_queryset_mixin_fallback() -> None:
    """Falls back to the default queryset for unmapped actions."""

    class FakeView(mixins.ActionToQuerysetMixin):
        queryset = 'default_qs'
        querysets = {'list': 'list_qs'}
        action = 'retrieve'

    view = FakeView()
    assert view.get_queryset() == 'default_qs'


def test_action_to_serializer_mixin_matched() -> None:
    """Returns the action-specific serializer class when the action matches."""

    class FakeView(mixins.ActionToSerializerMixin):
        serializer_class = 'DefaultSerializer'
        serializers_classes = {'list': 'ListSerializer'}
        action = 'list'

    view = FakeView()
    assert view.get_serializer_class() == 'ListSerializer'


def test_action_to_serializer_mixin_fallback() -> None:
    """Falls back to the default serializer class for unmapped actions."""

    class FakeView(mixins.ActionToSerializerMixin):
        serializer_class = 'DefaultSerializer'
        serializers_classes = {'list': 'ListSerializer'}
        action = 'create'

    view = FakeView()
    assert view.get_serializer_class() == 'DefaultSerializer'


def test_method_to_queryset_mixin_matched() -> None:
    """Returns the method-specific queryset when the HTTP method matches."""

    class FakeView(mixins.MethodToQuerysetMixin):
        queryset = 'default_qs'
        querysets = {'GET': 'get_qs', 'POST': 'post_qs'}
        request = MagicMock(method='GET')

    view = FakeView()
    assert view.get_queryset() == 'get_qs'


def test_method_to_queryset_mixin_fallback() -> None:
    """Falls back to the default queryset for unmapped HTTP methods."""

    class FakeView(mixins.MethodToQuerysetMixin):
        queryset = 'default_qs'
        querysets = {'GET': 'get_qs'}
        request = MagicMock(method='DELETE')

    view = FakeView()
    assert view.get_queryset() == 'default_qs'


def test_method_to_serializer_mixin_matched() -> None:
    """Returns the method-specific serializer class when the HTTP method matches."""

    class FakeView(mixins.MethodToSerializerMixin):
        serializer_class = 'DefaultSerializer'
        serializers_classes = {'POST': 'PostSerializer'}
        request = MagicMock(method='POST')

    view = FakeView()
    assert view.get_serializer_class() == 'PostSerializer'


def test_method_to_serializer_mixin_fallback() -> None:
    """Falls back to the default serializer class for unmapped HTTP methods."""

    class FakeView(mixins.MethodToSerializerMixin):
        serializer_class = 'DefaultSerializer'
        serializers_classes = {'POST': 'PostSerializer'}
        request = MagicMock(method='GET')

    view = FakeView()
    assert view.get_serializer_class() == 'DefaultSerializer'


def test_redirect_to_login_mixin_authenticated() -> None:
    """Authenticated users get the original response, no redirect."""

    class Base:
        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        pass

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
        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        pass

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
        def finalize_response(self, request, response, *args, **kwargs):  # pylint:disable=unused-argument
            return response

    class FakeView(mixins.RedirectToLoginMixin, Base):
        pass

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
