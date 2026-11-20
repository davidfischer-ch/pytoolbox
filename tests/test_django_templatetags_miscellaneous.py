"""Tests for the django.templatetags.miscellaneous module."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

import os
from datetime import time, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from django.db import models
from django.test import override_settings

from pytoolbox.django import templatetags


def test_getattribute_numeric_index() -> None:
    """Numeric string attribute retrieves by index from a sequence."""
    assert templatetags.getattribute(['a', 'b', 'c'], '1') == 'b'


def test_getattribute_object_attr() -> None:
    """String attribute retrieves the named attribute from an object."""
    obj = MagicMock()
    obj.name = 'hello'
    assert templatetags.getattribute(obj, 'name') == 'hello'


def test_getattribute_missing_returns_invalid() -> None:
    """Missing attribute returns the configured string_if_invalid value."""
    assert templatetags.getattribute({}, 'missing') == templatetags.string_if_invalid


def test_inline_reads_a_file_in_static_root(tmp_path: Path) -> None:
    """A file in STATIC_ROOT is inlined."""
    (static_root := tmp_path / 'static').mkdir()
    (static_root / 'app.js').write_text('content', encoding='utf-8')
    with override_settings(STATIC_ROOT=str(static_root)):
        assert templatetags.inline(str(static_root / 'app.js')) == 'content'


def test_inline_of_a_file_beside_static_root_is_invalid(tmp_path: Path) -> None:
    """A file in a sibling directory whose name starts with STATIC_ROOT's is not inlined."""
    (static_root := tmp_path / 'static').mkdir()
    (private := tmp_path / 'static-private').mkdir()
    (private / 'secret.txt').write_text('secret', encoding='utf-8')
    with override_settings(DEBUG=False, STATIC_ROOT=str(static_root)):
        assert templatetags.inline(str(private / 'secret.txt')) == templatetags.string_if_invalid


def test_inline_of_a_link_out_of_static_root_is_invalid(tmp_path: Path) -> None:
    """A symbolic link in STATIC_ROOT to a file outside of it is not inlined."""
    (static_root := tmp_path / 'static').mkdir()
    (tmp_path / 'secret.txt').write_text('secret', encoding='utf-8')
    (static_root / 'secret.txt').symlink_to(tmp_path / 'secret.txt')
    with override_settings(DEBUG=False, STATIC_ROOT=str(static_root)):
        assert (
            templatetags.inline(str(static_root / 'secret.txt')) == templatetags.string_if_invalid
        )


def test_rst_title() -> None:
    """Chapter and document levels produce correct rST markup."""
    result = templatetags.rst_title('Hello', 'chapter')
    assert result == f'Hello{os.linesep}{"=" * 5}{os.linesep}'
    result = templatetags.rst_title('Test', 'document')
    assert '====' in result


def test_rst_title_all_levels() -> None:
    """All rST title levels produce the correct underline/overline characters."""
    sep = os.linesep
    result = templatetags.rst_title('Sub', 'subtitle')
    assert result == f'---{sep}Sub{sep}---{sep}'
    result = templatetags.rst_title('Sec', 'section')
    assert result == f'Sec{sep}---{sep}'
    result = templatetags.rst_title('Sub', 'subsection')
    assert result == f'Sub{sep}~~~{sep}'
    assert templatetags.rst_title('X', 'invalid') == templatetags.string_if_invalid


def test_secs_to_time_none() -> None:
    """None input returns the invalid string marker."""
    assert templatetags.secs_to_time(None) == templatetags.string_if_invalid


def test_secs_to_time_none_defaults_to_zero() -> None:
    """None input with defaults_to_zero=True returns midnight (00:00:00)."""
    result = templatetags.secs_to_time(None, defaults_to_zero=True)
    assert isinstance(result, time)
    assert result.hour == 0 and result.minute == 0 and result.second == 0


def test_secs_to_time() -> None:
    """Seconds are converted to a time object with correct hour and minute."""
    result = templatetags.secs_to_time(3661.5)
    assert isinstance(result, time)
    assert result.hour == 1
    assert result.minute == 1


def test_status_label() -> None:
    """Status string is wrapped in a span with the matching Bootstrap label class."""
    result = templatetags.status_label('error')
    assert 'label-important' in result
    assert 'ERROR' in result


def test_timedelta_filter() -> None:
    """Formats seconds and timedelta objects as human-readable duration strings."""
    assert templatetags.timedelta(6316.9) == '1:45:17'
    assert templatetags.timedelta(timedelta(days=10, hours=2)) == '10 days, 2:00:00'
    assert templatetags.timedelta(None) == templatetags.string_if_invalid


def test_verbose_name() -> None:
    """Returns the model's singular verbose name."""

    class MyModel(models.Model):
        """Test model class."""

        class Meta:
            """Test class."""

            app_label = 'test'
            verbose_name = 'my model'

    instance = MyModel.__new__(MyModel)
    assert templatetags.verbose_name(instance) == 'my model'


def test_verbose_name_plural() -> None:
    """Returns the model's plural verbose name."""

    class MyModel(models.Model):
        """Test model class."""

        class Meta:
            """Meta class."""

            app_label = 'test'
            verbose_name = 'my model'
            verbose_name_plural = 'my models'

    instance = MyModel.__new__(MyModel)
    assert templatetags.verbose_name_plural(instance) == 'my models'
    assert templatetags.verbose_name_plural(None) == templatetags.string_if_invalid
