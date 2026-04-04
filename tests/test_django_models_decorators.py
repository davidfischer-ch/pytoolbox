"""Tests for the django.models.decorators module."""

# pylint:disable=no-member,too-few-public-methods
from __future__ import annotations

from unittest.mock import patch

import pytest

from pytoolbox.django.models import decorators


def test_with_urls_no_actions_raises() -> None:
    """Raises ValueError when no interface_actions are provided."""
    with pytest.raises(ValueError, match='At least one action'):
        decorators.with_urls('myapp')


def test_with_urls_unknown_kwargs_raises() -> None:
    """Raises AttributeError for unknown keyword arguments."""
    with pytest.raises(AttributeError):
        decorators.with_urls('myapp', 'detail', unknown=True)


def test_with_urls_creates_detail_url() -> None:
    """Adds get_detail_url that calls reverse with pk argument."""

    class MyModel:
        """Test class."""

        pk = 42

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/myapp/42/detail',
    ) as mock_reverse:
        decorated = decorators.with_urls('myapp', 'detail')(MyModel)
        obj = decorated()
        url = obj.get_detail_url()
        mock_reverse.assert_called_with('myapp:detail', args=['42'])
        assert url == '/myapp/42/detail'


def test_with_urls_sets_absolute_url() -> None:
    """When 'detail' is an action, get_absolute_url is set to get_detail_url."""

    class MyModel:
        """Test class."""

        pk = 1

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/url',
    ):
        decorated = decorators.with_urls('myapp', 'detail')(MyModel)
        assert decorated.get_absolute_url is decorated.get_detail_url


def test_with_urls_create_action() -> None:
    """The 'create' action adds a classmethod that calls reverse without pk."""

    class MyModel:
        """Test class."""

        pk = 1

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/myapp/create',
    ) as mock_reverse:
        decorated = decorators.with_urls('myapp', 'create')(MyModel)
        url = decorated.get_create_url()
        mock_reverse.assert_called_with('myapp:create')
        assert url == '/myapp/create'


def test_with_urls_singleton() -> None:
    """Singleton actions call reverse without pk arguments."""

    class MyModel:
        """Test class."""

        pk = 1

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/myapp/detail',
    ) as mock_reverse:
        decorated = decorators.with_urls(
            'myapp',
            'detail',
            singleton=True,
        )(MyModel)
        obj = decorated()
        url = obj.get_detail_url()
        mock_reverse.assert_called_with('myapp:detail')
        assert url == '/myapp/detail'


def test_with_urls_skips_existing_method() -> None:
    """Does not overwrite a method that already exists on the model."""

    class MyModel:
        """Test class."""

        pk = 1

        def get_detail_url(self):
            """Test method."""
            return '/custom'

    with patch(
        'pytoolbox.django.models.decorators.reverse',
    ):
        decorated = decorators.with_urls('myapp', 'detail')(MyModel)
        obj = decorated()
        assert obj.get_detail_url() == '/custom'


def test_with_urls_interface_actions() -> None:
    """interface_actions attribute is set on the decorated model."""

    class MyModel:
        """Test class."""

        pk = 1

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/url',
    ):
        decorated = decorators.with_urls(
            'myapp',
            'detail',
            'update',
        )(MyModel)
        assert decorated.interface_actions == ('detail', 'update')


def test_with_urls_no_absolute_url_without_detail() -> None:
    """get_absolute_url is not set when 'detail' is not an action."""

    class MyModel:
        """Test class."""

        pk = 1

    with patch(
        'pytoolbox.django.models.decorators.reverse',
        return_value='/url',
    ):
        decorated = decorators.with_urls('myapp', 'update')(MyModel)
        assert not hasattr(decorated, 'get_absolute_url')
