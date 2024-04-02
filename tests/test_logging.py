from __future__ import annotations

import logging
from unittest import mock

from pytest import raises

from pytoolbox.logging import get_logger


def test_get_logger_from_callable() -> None:
    func = mock.Mock(return_value=None)
    func.__name__ = 'func'
    log = get_logger(func)
    assert isinstance(log, logging.Logger)
    assert log.name == 'unittest.mock.func'
    assert log.level == logging.NOTSET
    log.debug('Some message')
    func.assert_called_once_with('Some message')


def test_get_logger_from_logger() -> None:
    assert get_logger(logging.getLogger(__name__)) is get_logger(__name__)
    assert get_logger(get_logger(__name__)) is get_logger(__name__)


def test_get_logger_from_none() -> None:
    with raises(NotImplementedError, match='Logging with None'):
        get_logger(None)
