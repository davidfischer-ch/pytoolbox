"""Tests for the django_datatable_view.views.mixins module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from datatableview.views import DatatableView
from django.contrib.auth.models import User
from django.test import RequestFactory

from pytoolbox.django_datatable_view.views import mixins

pytestmark = pytest.mark.filterwarnings('ignore:MultiTablesMixin is deprecated:DeprecationWarning')


def test_multi_tables_get_datatable_name_from_arg() -> None:
    """Explicit name argument takes priority over request parameters."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        request = MagicMock()

    view = FakeView()
    assert view.get_datatable_name('custom') == 'custom'


def test_multi_tables_get_datatable_name_from_request() -> None:
    """Falls back to the datatable-name GET parameter when no argument is given."""

    class FakeView(mixins.MultiTablesMixin):
        """Test class."""

        request = MagicMock()

    view = FakeView()
    view.request.GET = {'datatable-name': 'from-request'}
    assert view.get_datatable_name(None) == 'from-request'


def test_multi_tables_get_datatable_name_default() -> None:
    """Returns 'default' when neither argument nor request parameter is present."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        request = MagicMock()

    view = FakeView()
    view.request.GET = {}
    assert view.get_datatable_name(None) == 'default'


def test_multi_tables_get_ajax_url() -> None:
    """Builds an AJAX URL with the datatable-name query parameter appended."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        request = MagicMock()

    view = FakeView()
    view.request.path = '/my/view/'
    view.request.GET = {}
    url = view.get_ajax_url('table1')
    assert url == '/my/view/?datatable-name=table1'


def test_multi_tables_get_ajax_url_default() -> None:
    """Uses 'default' as the datatable name when none is specified."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        request = MagicMock()

    view = FakeView()
    view.request.path = '/my/view/'
    view.request.GET = {}
    url = view.get_ajax_url()
    assert url == '/my/view/?datatable-name=default'


def test_multi_tables_get_queryset_valid_name() -> None:
    """Dispatches to the table-specific get_<name>_queryset method."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        multi_datatables = (('default', 'Default'), ('other', 'Other'))
        request = MagicMock()

        def get_default_queryset(self, qs):  # pylint:disable=unused-argument
            """Get default queryset implementation."""
            return 'default_filtered'

    class Base:
        """Test class."""

        def get_queryset(self):
            """Test method."""
            return 'base_qs'

    class TestView(FakeView, Base):
        """Test view combining FakeView and Base."""

    view = TestView()
    view.request.GET = {}
    assert view.get_queryset() == 'default_filtered'


def test_multi_tables_get_queryset_bad_name_returns_none() -> None:
    """Returns an empty queryset for unregistered datatable names."""

    class FakeView(mixins.MultiTablesMixin):
        """Test view with MultiTablesMixin."""

        multi_datatables = (('default', 'Default'),)
        request = MagicMock()

    class Base:
        """Test class."""

        def get_queryset(self):
            """Test method."""
            qs = MagicMock()
            qs.none.return_value = 'empty_qs'
            return qs

    class TestView(FakeView, Base):
        """Test view combining FakeView and Base."""

    view = TestView()
    view.request.GET = {'datatable-name': 'nonexistent'}
    assert view.get_queryset() == 'empty_qs'


def test_multi_tables_builds_each_datatable_on_a_datatable_view() -> None:
    """On a DatatableView, each datatable gets its own queryset and its own AJAX URL."""

    class UsersView(mixins.MultiTablesMixin, DatatableView):
        """View listing the active users and the staff."""

        model = User
        multi_datatables = (('default', 'Active'), ('staff', 'Staff'))

        def get_default_queryset(self, queryset):
            """Return the active users."""
            return queryset.filter(is_active=True)

        def get_staff_queryset(self, queryset):
            """Return the staff."""
            return queryset.filter(is_staff=True)

    response = UsersView.as_view()(RequestFactory().get('/users/'))
    tables = {name: table for name, _, table in response.context_data['datatables']}
    assert tables['default'].url == '/users/?datatable-name=default'
    assert tables['staff'].url == '/users/?datatable-name=staff'
    assert str(tables['default'].object_list.query) == str(
        User.objects.filter(is_active=True).query
    )
    assert str(tables['staff'].object_list.query) == str(User.objects.filter(is_staff=True).query)


def test_multi_tables_subclass_is_deprecated() -> None:
    """Subclassing MultiTablesMixin emits a DeprecationWarning naming its replacement."""
    with pytest.warns(DeprecationWarning, match='MultipleDatatableMixin'):

        class FakeView(mixins.MultiTablesMixin):  # pylint:disable=unused-variable
            """Test view with MultiTablesMixin."""
