"""Tests for the logging module."""

from __future__ import annotations

import logging as stdlib_logging
from unittest import mock

import pytest
from pytest import raises

from pytoolbox import logging


@pytest.fixture(autouse=True)
def _force_color(monkeypatch):
    monkeypatch.setenv('FORCE_COLOR', 'yes')
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.delenv('ANSI_COLORS_DISABLED', raising=False)


def test_get_logger_from_callable() -> None:
    """get_logger() creates a logger that calls the provided callable."""
    func = mock.Mock(return_value=None)
    func.__name__ = 'func'
    log = logging.get_logger(func)
    assert isinstance(log, stdlib_logging.Logger)
    assert log.name == 'unittest.mock.func'
    assert log.level == stdlib_logging.NOTSET
    log.debug('Some message')
    func.assert_called_once_with('Some message')


def test_get_logger_from_logger() -> None:
    """get_logger() returns the same logger for equivalent inputs."""
    assert logging.get_logger(stdlib_logging.getLogger(__name__)) is logging.get_logger(__name__)
    assert logging.get_logger(logging.get_logger(__name__)) is logging.get_logger(__name__)


def test_get_logger_from_none() -> None:
    """get_logger() raises NotImplementedError when called with None."""
    with raises(NotImplementedError, match='Logging with None'):
        logging.get_logger(None)


def test_setup_logging_colorize_only_on_console_handler() -> None:
    """setup_logging() applies ColorizeFormatter only to console handler."""
    log = logging.setup_logging(
        'test_colorize_console',
        reset=True,
        console=True,
        colorize=True,
    )
    console_handler = log.handlers[0]
    assert isinstance(console_handler.formatter, logging.ColorizeFormatter)


def test_setup_logging_file_handler_not_colorized(tmp_path) -> None:
    """setup_logging() does not colorize file handlers."""
    log = logging.setup_logging(
        'test_colorize_file',
        reset=True,
        path=tmp_path / 'test.log',
        console=True,
        colorize=True,
    )
    file_handler = log.handlers[0]
    console_handler = log.handlers[1]
    assert not isinstance(file_handler.formatter, logging.ColorizeFormatter)
    assert isinstance(console_handler.formatter, logging.ColorizeFormatter)


def test_setup_logging_child_logger_gets_colorized(tmp_path) -> None:
    """setup_logging() colorizes child loggers but not file output."""
    logging.setup_logging(
        'test_parent',
        reset=True,
        path=tmp_path / 'test.log',
        console=True,
        colorize=True,
    )
    child = stdlib_logging.getLogger('test_parent.child')
    child.setLevel(stdlib_logging.DEBUG)
    child.warning('colored warning')
    # File should have no ANSI codes
    content = (tmp_path / 'test.log').read_text()
    assert '\x1b[' not in content
    assert 'colored warning' in content


def test_colorize_formatter_warning() -> None:
    """ColorizeFormatter applies yellow color to WARNING level."""
    formatter = logging.ColorizeFormatter()
    record = stdlib_logging.LogRecord(
        name='test',
        level=stdlib_logging.WARNING,
        pathname='',
        lineno=0,
        msg='Attention',
        args=(),
        exc_info=None,
    )
    result = formatter.format(record)
    assert '\x1b[33m' in result
    assert 'Attention' in result
    assert result.endswith('\x1b[0m')


def test_colorize_formatter_error() -> None:
    """ColorizeFormatter applies red color to ERROR level."""
    formatter = logging.ColorizeFormatter()
    record = stdlib_logging.LogRecord(
        name='test',
        level=stdlib_logging.ERROR,
        pathname='',
        lineno=0,
        msg='Boom',
        args=(),
        exc_info=None,
    )
    result = formatter.format(record)
    assert '\x1b[31m' in result
    assert 'Boom' in result


def test_colorize_formatter_no_color_for_unknown_level() -> None:
    """ColorizeFormatter does not apply color to levels without color mapping."""
    formatter = logging.ColorizeFormatter()
    record = stdlib_logging.LogRecord(
        name='test',
        level=stdlib_logging.CRITICAL,
        pathname='',
        lineno=0,
        msg='Fatal',
        args=(),
        exc_info=None,
    )
    result = formatter.format(record)
    assert '\x1b[' not in result
    assert 'Fatal' in result


def test_colorize_formatter_custom_color_by_level() -> None:
    """ColorizeFormatter uses custom color mapping when provided."""
    formatter = logging.ColorizeFormatter(
        color_by_level={stdlib_logging.CRITICAL: 'magenta'},
    )
    record = stdlib_logging.LogRecord(
        name='test',
        level=stdlib_logging.CRITICAL,
        pathname='',
        lineno=0,
        msg='Fatal',
        args=(),
        exc_info=None,
    )
    result = formatter.format(record)
    assert '\x1b[35m' in result


def test_colorize_formatter_does_not_mutate_record() -> None:
    """ColorizeFormatter does not modify the original log record."""
    formatter = logging.ColorizeFormatter()
    record = stdlib_logging.LogRecord(
        name='test',
        level=stdlib_logging.WARNING,
        pathname='',
        lineno=0,
        msg='Keep me clean',
        args=(),
        exc_info=None,
    )
    formatter.format(record)
    assert record.msg == 'Keep me clean'
