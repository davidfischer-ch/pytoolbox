# pylint:disable=no-value-for-parameter,unnecessary-dunder-call
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
    """Calling a deprecated function emits a DeprecationWarning with name and guidelines."""

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


def test_hybridmethod_class_level_access() -> None:
    """Hybridmethod called on the class receives the class."""

    class MyClass:
        value = 'class_val'

        @decorators.hybridmethod
        def get_value(receiver):  # pylint:disable=no-self-argument  # noqa: N805
            return receiver.value

    assert MyClass.get_value() == 'class_val'


def test_hybridmethod_instance_level_access() -> None:
    """Hybridmethod called on an instance receives the instance."""

    class MyClass:
        value = 'class_val'

        def __init__(self):
            self.value = 'instance_val'

        @decorators.hybridmethod
        def get_value(receiver):  # pylint:disable=no-self-argument  # noqa: N805
            return receiver.value

    assert MyClass().get_value() == 'instance_val'


def test_hybridmethod_has_func_and_self() -> None:
    """The bound hybrid callable exposes __func__ and __self__."""

    class MyClass:
        @decorators.hybridmethod
        def method(receiver):  # pylint:disable=no-self-argument  # noqa: N805
            return 42

    bound = MyClass.__dict__['method'].__get__(None, MyClass)
    assert hasattr(bound, '__func__')
    assert bound.__self__ is MyClass


def test_hybridmethod_instance_self() -> None:
    """__self__ on an instance-bound hybrid is the instance."""

    class MyClass:
        @decorators.hybridmethod
        def method(receiver):  # pylint:disable=no-self-argument  # noqa: N805
            return 42

    obj = MyClass()
    bound = MyClass.__dict__['method'].__get__(obj, MyClass)
    assert bound.__self__ is obj


def test_hybridmethod_with_args() -> None:
    """Hybridmethod passes extra positional and keyword args."""

    class MyClass:
        @decorators.hybridmethod
        def add(receiver, a, b=0):  # pylint:disable=no-self-argument  # noqa: N805
            return a + b

    assert MyClass.add(3, b=7) == 10


def test_confirm_it_proceeds() -> None:
    """When user confirms, the decorated function executes."""

    @decorators.confirm_it('Are you sure?')
    def do_thing():
        return 'done'

    with patch.object(
        decorators.console,
        'confirm',
        return_value=True,
    ):
        assert do_thing() == 'done'


def test_confirm_it_aborts(capsys) -> None:
    """When user declines, abort message is printed."""

    @decorators.confirm_it('Are you sure?', abort_message='Nope')
    def do_thing():
        return 'done'

    with patch.object(
        decorators.console,
        'confirm',
        return_value=False,
    ):
        result = do_thing()
        assert result is None
        assert 'Nope' in capsys.readouterr().out


def test_confirm_it_default_abort_message(capsys) -> None:
    """Default abort message is printed when user declines."""

    @decorators.confirm_it('Sure?')
    def do_thing():
        return 'done'

    with patch.object(
        decorators.console,
        'confirm',
        return_value=False,
    ):
        do_thing()
        assert 'Operation aborted' in capsys.readouterr().out


def test_disable_iptables_stop_and_start() -> None:
    """When iptables stop succeeds, it is re-started after."""

    @decorators.disable_iptables
    def do_thing():
        return 'result'

    with (
        patch(
            'pytoolbox.subprocess.cmd',
        ) as mock_cmd,
        patch('builtins.print'),
    ):
        result = do_thing()
        assert result == 'result'
        assert mock_cmd.call_count == 2


def test_disable_iptables_not_available() -> None:
    """When iptables stop fails, start is not called."""

    @decorators.disable_iptables
    def do_thing():
        return 'result'

    with (
        patch(
            'pytoolbox.subprocess.cmd',
            side_effect=RuntimeError('no iptables'),
        ) as mock_cmd,
        patch('builtins.print'),
    ):
        result = do_thing()
        assert result == 'result'
        # cmd called once for stop (which failed), not for start
        assert mock_cmd.call_count == 1


def test_cached_property_caches_on_instance() -> None:
    """Value is computed once and stored in instance __dict__."""
    call_count = 0

    class MyClass:
        @decorators.cached_property
        def expensive(self):
            nonlocal call_count
            call_count += 1
            return 42

    obj = MyClass()
    assert obj.expensive == 42
    assert obj.expensive == 42
    assert call_count == 1
    assert 'expensive' in obj.__dict__


def test_cached_property_class_access_returns_descriptor() -> None:
    """Accessing via the class returns the descriptor itself."""

    class MyClass:
        @decorators.cached_property
        def prop(self):
            return 99

    assert isinstance(MyClass.prop, decorators.cached_property)
