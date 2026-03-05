from __future__ import annotations

from unittest.mock import MagicMock

from pytoolbox.django_datatable_view.views import mixins


def test_multi_tables_get_datatable_name_from_arg() -> None:
    class FakeView(mixins.MultiTablesMixin):
        request = MagicMock()

    view = FakeView()
    assert view.get_datatable_name('custom') == 'custom'


def test_multi_tables_get_datatable_name_from_request() -> None:
    class FakeView(mixins.MultiTablesMixin):
        request = MagicMock()

    view = FakeView()
    view.request.GET = {'datatable-name': 'from-request'}
    assert view.get_datatable_name(None) == 'from-request'


def test_multi_tables_get_datatable_name_default() -> None:
    class FakeView(mixins.MultiTablesMixin):
        request = MagicMock()

    view = FakeView()
    view.request.GET = {}
    assert view.get_datatable_name(None) == 'default'


def test_multi_tables_get_ajax_url() -> None:
    class FakeView(mixins.MultiTablesMixin):
        request = MagicMock()

    view = FakeView()
    view.request.path = '/my/view/'
    view.request.GET = {}
    url = view.get_ajax_url('table1')
    assert url == '/my/view/?datatable-name=table1'


def test_multi_tables_get_ajax_url_default() -> None:
    class FakeView(mixins.MultiTablesMixin):
        request = MagicMock()

    view = FakeView()
    view.request.path = '/my/view/'
    view.request.GET = {}
    url = view.get_ajax_url()
    assert url == '/my/view/?datatable-name=default'


def test_multi_tables_get_queryset_valid_name() -> None:
    class FakeView(mixins.MultiTablesMixin):
        multi_datatables = (('default', 'Default'), ('other', 'Other'))
        request = MagicMock()

        def get_default_queryset(self, qs):  # pylint:disable=unused-argument
            return 'default_filtered'

    class Base:
        def get_queryset(self):
            return 'base_qs'

    class TestView(FakeView, Base):
        pass

    view = TestView()
    view.request.GET = {}
    assert view.get_queryset() == 'default_filtered'


def test_multi_tables_get_queryset_bad_name_returns_none() -> None:
    class FakeView(mixins.MultiTablesMixin):
        multi_datatables = (('default', 'Default'),)
        request = MagicMock()

    class Base:
        def get_queryset(self):
            qs = MagicMock()
            qs.none.return_value = 'empty_qs'
            return qs

    class TestView(FakeView, Base):
        pass

    view = TestView()
    view.request.GET = {'datatable-name': 'nonexistent'}
    assert view.get_queryset() == 'empty_qs'


def test_multi_tables_get_context_data() -> None:
    class Base:
        def get_context_data(self, **kwargs):  # pylint:disable=unused-argument
            return {'datatable': 'default_table', 'extra': 'data'}

    class FakeView(mixins.MultiTablesMixin, Base):
        multi_datatables = (('default', 'Default Table'),)
        request = MagicMock()

    view = FakeView()
    view.request.path = '/view/'
    view.request.GET = {}
    view.datatable_structure_class = MagicMock()

    context = view.get_context_data()
    assert 'datatables' in context
    assert 'datatable' not in context  # popped
    assert context['extra'] == 'data'
    assert len(context['datatables']) == 1
    name, label, table = context['datatables'][0]
    assert name == 'default'
    assert label == 'Default Table'
    assert table == 'default_table'
