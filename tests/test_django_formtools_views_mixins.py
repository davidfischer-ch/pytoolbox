"""Tests for the django_formtools.views.mixins module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytoolbox.django_formtools.views import mixins


def test_datatable_view_ajax_detection() -> None:
    """AJAX requests (X-Requested-With header) are delegated to the table view."""

    class FakeView(mixins.DataTableViewCompositionMixin):
        """Test view class."""

        table_view_classes = {'step1': MagicMock}
        """Test class."""
        steps = MagicMock(current='step1')

        def __init__(self):
            self.request = MagicMock()
            self.request.headers = {}

    view = FakeView()
    view.request.headers = {}
    with patch.object(view, 'get_table_view') as get_table:
        try:
            view.get(view.request)
        except (AttributeError, TypeError):
            pass
        get_table.assert_not_called()

    view.request.headers = {'X-Requested-With': 'XMLHttpRequest'}
    table_view = MagicMock()
    with patch.object(view, 'get_table_view', return_value=table_view):
        result = view.get(view.request)
        assert result == table_view.get_ajax.return_value


def test_datatable_view_get_table_view_returns_none_for_unknown_step() -> None:
    """Returns None when no table view is registered for the current step."""

    class FakeView(mixins.DataTableViewCompositionMixin):
        """Test class."""

        table_view_classes = {'step1': MagicMock}
        steps = MagicMock(current='unknown_step')

    view = FakeView()
    assert view.get_table_view() is None


def test_datatable_view_get_table_view_returns_instance() -> None:
    """Returns an instantiated table view with request and object_list set."""
    mock_class = MagicMock()

    class FakeView(mixins.DataTableViewCompositionMixin):
        """Test class."""

        table_view_classes = {'step1': mock_class}
        steps = MagicMock(current='step1')

        def __init__(self):
            self.request = MagicMock()

    view = FakeView()
    result = view.get_table_view()
    mock_class.assert_called_once()
    assert result.request is view.request
    assert result.object_list is None


def test_datatable_view_get_context_data_with_table() -> None:
    """Context is updated with the table view's context when a table view exists."""

    class Base:
        """Test class."""

        def get_context_data(self, **kwargs):  # pylint:disable=unused-argument
            """Get context data implementation."""
            return {'key': 'value'}

    class FakeView(mixins.DataTableViewCompositionMixin, Base):
        """Test view class."""

        table_view_classes = {'step1': MagicMock}
        steps = MagicMock(current='step1')

        def __init__(self):
            self.request = MagicMock()

    view = FakeView()
    context = view.get_context_data()
    assert 'key' in context


def test_datatable_view_get_context_data_without_table() -> None:
    """Context is unchanged when no table view exists for the current step."""

    class Base:
        """Test class."""

        def get_context_data(self, **kwargs):  # pylint:disable=unused-argument
            """Get context data implementation."""
            return {'key': 'value'}

    class FakeView(mixins.DataTableViewCompositionMixin, Base):
        """Test view class."""

        table_view_classes = {}
        steps = MagicMock(current='step1')

    view = FakeView()
    context = view.get_context_data()
    assert context == {'key': 'value'}


def test_serialize_step_instance_mixin_serialized_instances() -> None:
    """serialized_instances lazily creates and caches the storage dict."""

    class FakeView(mixins.SerializeStepInstanceMixin):
        """Test view class."""

        steps = MagicMock(current='step1')

        def __init__(self):
            self.storage = MagicMock()
            self.storage.extra_data = {}

    view = FakeView()
    instances = view.serialized_instances
    assert instances == {}
    assert 'serialized-instances' in view.storage.extra_data
    assert view.serialized_instances is instances


def test_serialize_step_instance_mixin_get_form_kwargs() -> None:
    """Serialized instance data is merged into form kwargs for the matching step."""

    class Base:
        """Test class."""

        def get_form_kwargs(self, step):  # pylint:disable=unused-argument
            """Get form kwargs implementation."""
            return {'initial': {}}

    class FakeView(mixins.SerializeStepInstanceMixin, Base):
        """Test view class."""

        steps = MagicMock(current='step1')

        def __init__(self):
            self.storage = MagicMock()
            self.storage.extra_data = {
                'serialized-instances': {'step1': {'data': 'serialized'}},
            }

    view = FakeView()
    kwargs = view.get_form_kwargs('step1')
    assert kwargs['data'] == 'serialized'
    assert kwargs['initial'] == {}


def test_serialize_step_instance_mixin_get_form_kwargs_no_serialized() -> None:
    """Form kwargs are unchanged when no serialized instance exists for the step."""

    class Base:
        """Test class."""

        def get_form_kwargs(self, step):  # pylint:disable=unused-argument
            """Get form kwargs implementation."""
            return {'initial': {}}

    class FakeView(mixins.SerializeStepInstanceMixin, Base):
        """Test view class."""

        steps = MagicMock(current='step1')

        def __init__(self):
            self.storage = MagicMock()
            self.storage.extra_data = {'serialized-instances': {}}

    view = FakeView()
    kwargs = view.get_form_kwargs('step2')
    assert kwargs == {'initial': {}}


def test_serialize_step_instance_mixin_get_form() -> None:
    """get_form() swaps the form class to SerializedInstanceForm for serialized steps."""
    sentinel_form = MagicMock()

    class Base:
        """Test class."""

        def get_form(self, step=None, *args, **kwargs):  # pylint:disable=unused-argument,keyword-arg-before-vararg
            """Get form implementation."""
            return sentinel_form

    class FakeView(mixins.SerializeStepInstanceMixin, Base):
        """Test view class."""

        steps = MagicMock(current='step1')

        def __init__(self):
            self.storage = MagicMock()
            self.storage.extra_data = {
                'serialized-instances': {'step1': {'pk': 1}},
            }
            self.form_list = {}

    view = FakeView()
    result = view.get_form()
    assert view.form_list['step1'] is view.serialized_instance_form_class
    assert result is sentinel_form


def test_serialize_step_instance_mixin_get_form_no_serialized() -> None:
    """get_form() leaves form_list unchanged for steps without serialized data."""
    sentinel_form = MagicMock()

    class Base:
        """Test class."""

        def get_form(self, step=None, *args, **kwargs):  # pylint:disable=unused-argument,keyword-arg-before-vararg
            """Get form implementation."""
            return sentinel_form

    class FakeView(mixins.SerializeStepInstanceMixin, Base):
        """Test view class."""

        steps = MagicMock(current='step2')

        def __init__(self):
            self.storage = MagicMock()
            self.storage.extra_data = {'serialized-instances': {}}
            self.form_list = {}

    view = FakeView()
    result = view.get_form()
    assert 'step2' not in view.form_list
    assert result is sentinel_form
