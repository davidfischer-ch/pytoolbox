from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {'string_if_invalid': ''}
        }],
        STATIC_ROOT='/static',
        DEBUG=True)
    django.setup()


def test_getattribute_has_key_dead_code() -> None:
    """has_key doesn't exist in Python 3, so the branch is dead code."""
    from pytoolbox.django.templatetags import getattribute
    # A dict should be accessed via its attribute, not via the dead has_key branch
    result = getattribute({'name': 'value'}, 'name')
    assert result == 'value'
    # Confirm dicts don't have has_key in Python 3
    assert not hasattr({}, 'has_key')


def test_getattribute_numeric_index() -> None:
    from pytoolbox.django.templatetags import getattribute
    assert getattribute(['a', 'b', 'c'], '1') == 'b'


def test_getattribute_object_attr() -> None:
    from pytoolbox.django.templatetags import getattribute
    obj = MagicMock()
    obj.name = 'hello'
    assert getattribute(obj, 'name') == 'hello'


def test_inline_closes_file_handle() -> None:
    """inline filter should not leak file handles."""
    from pytoolbox.django.templatetags import inline
    filepath = '/static/test.js'
    with (
        patch('pytoolbox.django.templatetags._include_is_allowed', return_value=True),
        patch('builtins.open', mock_open(read_data='content')) as mocked_open
    ):
        result = inline(filepath)
        assert result == 'content'
        handle = mocked_open()
        handle.__exit__.assert_called()


def test_faster_validate_on_save_mixin_uses_is_relation() -> None:
    """FasterValidateOnSaveMixin should use f.is_relation instead of removed f.rel."""
    from django.db import models
    from pytoolbox.django.models.mixins import FasterValidateOnSaveMixin

    class TestModel(FasterValidateOnSaveMixin, models.Model):
        name = models.CharField(max_length=100)
        other = models.ForeignKey(
            'auth.User',
            on_delete=models.CASCADE,
            null=True)

        class Meta:
            app_label = 'test'

    instance = TestModel.__new__(TestModel)
    kwargs = instance.validate_on_save_kwargs
    # The FK 'other' (plus auto 'other_id') should be excluded
    assert 'other' in kwargs['exclude']
    # The regular field 'name' should NOT be excluded
    assert 'name' not in kwargs['exclude']


def test_datatable_view_ajax_detection() -> None:
    """DataTableViewCompositionMixin.get should use headers instead of removed is_ajax()."""
    from pytoolbox.django_formtools.views.mixins import DataTableViewCompositionMixin

    class FakeView(DataTableViewCompositionMixin):
        table_view_classes = {'step1': MagicMock}
        steps = MagicMock(current='step1')

        def __init__(self):
            self.request = MagicMock()
            self.request.headers = {}

    view = FakeView()
    # Non-AJAX request should not call get_table_view's get_ajax
    view.request.headers = {}
    with patch.object(view, 'get_table_view') as get_table:
        # super().get() will fail but we only care that get_table_view is not called
        try:
            view.get(view.request)
        except (AttributeError, TypeError):
            pass
        get_table.assert_not_called()

    # AJAX request should delegate to table view
    view.request.headers = {'X-Requested-With': 'XMLHttpRequest'}
    table_view = MagicMock()
    with patch.object(view, 'get_table_view', return_value=table_view):
        result = view.get(view.request)
        assert result == table_view.get_ajax.return_value
