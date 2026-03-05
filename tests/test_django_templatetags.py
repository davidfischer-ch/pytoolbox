from __future__ import annotations

import datetime
import os
from unittest.mock import MagicMock, mock_open, patch

from django.db import models

from pytoolbox.django import templatetags


def test_getattribute_numeric_index() -> None:
    assert templatetags.getattribute(['a', 'b', 'c'], '1') == 'b'


def test_getattribute_object_attr() -> None:
    obj = MagicMock()
    obj.name = 'hello'
    assert templatetags.getattribute(obj, 'name') == 'hello'


def test_getattribute_missing_returns_invalid() -> None:
    assert templatetags.getattribute({}, 'missing') == templatetags.string_if_invalid


def test_inline_closes_file_handle() -> None:
    """inline filter should not leak file handles."""
    filepath = '/static/test.js'
    with (
        patch('pytoolbox.django.templatetags._include_is_allowed', return_value=True),
        patch('builtins.open', mock_open(read_data='content')) as mocked_open
    ):
        result = templatetags.inline(filepath)
        assert result == 'content'
        handle = mocked_open()
        handle.__exit__.assert_called()


def test_naturalbitrate() -> None:
    assert '16.5 Mb/s' in templatetags.naturalbitrate(16487211.33)
    assert templatetags.naturalbitrate(None) == templatetags.string_if_invalid


def test_naturalfilesize() -> None:
    assert '15.7 MB' in templatetags.naturalfilesize(16487211.33)
    assert templatetags.naturalfilesize(None) == templatetags.string_if_invalid


def test_rst_title() -> None:
    result = templatetags.rst_title('Hello', 'chapter')
    assert result == f'Hello{os.linesep}{"=" * 5}{os.linesep}'
    result = templatetags.rst_title('Test', 'document')
    assert '====' in result


def test_secs_to_time_none() -> None:
    assert templatetags.secs_to_time(None) == templatetags.string_if_invalid


def test_secs_to_time() -> None:
    result = templatetags.secs_to_time(3661.5)
    assert isinstance(result, datetime.time)
    assert result.hour == 1
    assert result.minute == 1


def test_status_label() -> None:
    result = templatetags.status_label('error')
    assert 'label-important' in result
    assert 'ERROR' in result


def test_timedelta_filter() -> None:
    assert templatetags.timedelta(6316.9) == '1:45:17'
    assert templatetags.timedelta(datetime.timedelta(days=10, hours=2)) == '10 days, 2:00:00'
    assert templatetags.timedelta(None) == templatetags.string_if_invalid


def test_rst_title_all_levels() -> None:
    sep = os.linesep
    result = templatetags.rst_title('Sub', 'subtitle')
    assert result == f'---{sep}Sub{sep}---{sep}'
    result = templatetags.rst_title('Sec', 'section')
    assert result == f'Sec{sep}---{sep}'
    result = templatetags.rst_title('Sub', 'subsection')
    assert result == f'Sub{sep}~~~{sep}'
    assert templatetags.rst_title('X', 'invalid') == templatetags.string_if_invalid


def test_verbose_name() -> None:
    class MyModel(models.Model):
        class Meta:
            app_label = 'test'
            verbose_name = 'my model'

    instance = MyModel.__new__(MyModel)
    assert templatetags.verbose_name(instance) == 'my model'


def test_verbose_name_plural() -> None:
    class MyModel(models.Model):
        class Meta:
            app_label = 'test'
            verbose_name = 'my model'
            verbose_name_plural = 'my models'

    instance = MyModel.__new__(MyModel)
    result = templatetags.verbose_name_plural(instance)
    # Note: verbose_name_plural currently has a bug - it uses verbose_name instead of
    # verbose_name_plural. This test documents the current behavior.
    assert result == 'my model'
    assert templatetags.verbose_name_plural(None) == templatetags.string_if_invalid
