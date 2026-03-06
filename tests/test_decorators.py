from __future__ import annotations

import os
import warnings
from unittest.mock import patch

import pytest

from pytoolbox import decorators


@decorators.run_once
def increment(counter: int) -> int:
    return counter + 1


@decorators.run_once
def decrement(counter: int) -> int:
    return counter - 1


def test_run_once() -> None:
    """Decorated function runs once then returns None; resetting executed flag re-enables it."""
    assert increment(0) == 1
    assert increment(0) is None
    assert decrement(1) == 0
    assert decrement(0) is None
    increment.executed = False  # type: ignore[attr-defined]
    assert increment(5.5) == 6.5
    assert increment(5.5) is None


def test_deprecated_emits_warning() -> None:
    """Calling a deprecated function emits a DeprecationWarning with function name and guidelines."""
    @decorators.deprecated('Use new_func instead')
    def old_func(x):
        return x + 1

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = old_func(5)
        assert result == 6
        assert len(caught) == 1
        assert issubclass(caught[0].category, DeprecationWarning)
        assert 'old_func' in str(caught[0].message)
        assert 'Use new_func instead' in str(caught[0].message)


def test_deprecated_without_guidelines() -> None:
    """Calling a deprecated function without guidelines omits the colon-separated suffix."""
    @decorators.deprecated()
    def old_func():
        return 42

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        assert old_func() == 42
        assert 'old_func' in str(caught[0].message)
        assert ':' not in str(caught[0].message).split('old_func')[1]


def test_root_required_raises_when_not_root() -> None:
    """Non-root user is blocked with RuntimeError."""
    @decorators.root_required()
    def privileged():
        return 'done'

    with patch.object(os, 'geteuid', return_value=1000):
        with pytest.raises(RuntimeError, match='root'):
            privileged()


def test_root_required_allows_root() -> None:
    """Root user (euid=0) can execute the decorated function."""
    @decorators.root_required()
    def privileged():
        return 'done'

    with patch.object(os, 'geteuid', return_value=0):
        assert privileged() == 'done'


def test_root_required_custom_message() -> None:
    """Custom error message is used when non-root user is blocked."""
    @decorators.root_required(error_message='Need sudo')
    def privileged():
        return 'done'

    with patch.object(os, 'geteuid', return_value=1000):
        with pytest.raises(RuntimeError, match='Need sudo'):
            privileged()
