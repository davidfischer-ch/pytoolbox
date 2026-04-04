"""Tests for the signals module."""

from __future__ import annotations

import os
import signal
import unittest

import pytest

from pytoolbox import exceptions, signals


class TestSignals(unittest.TestCase):
    """Test class for signal handling functionality."""

    def append_list_callback(self, number) -> None:
        """Append number to list and set flag."""
        self.flag = True
        self.list.append(number)

    def raise_handler(self, signum, frame) -> None:
        """Raise AssertionError when called."""
        raise AssertionError

    def set_flag_handler(self, signum, frame) -> None:  # pylint:disable=unused-argument
        """Set flag to True when called."""
        self.flag = True

    def set_flag_callback(self, *args, **kwargs) -> None:
        """Validate args and set flag to True."""
        assert args == (None,)
        assert not kwargs
        self.flag = True

    def setUp(self) -> None:
        # reset signal handlers
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self.name = self.flag = None
        self.list = []

    def tearDown(self) -> None:
        if self.name:
            assert self.flag is True, self.name
            if self.list:
                assert self.list == sorted(self.list), self.name

    def test_handler(self) -> None:
        """Registered handler is invoked when the signal is delivered."""
        self.name = 'test_handler'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_handler_reset(self) -> None:
        """reset=True replaces all previous handlers with the new one."""
        self.name = 'test_handler_reset'
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler, reset=True)
        signals.register_handler(signal.SIGTERM, self.set_flag_handler, reset=True)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback(self) -> None:
        """Registered callback is invoked with the specified args on signal delivery."""
        self.name = 'test_callback'
        signals.register_callback(signal.SIGTERM, self.set_flag_callback, args=[None])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callbacks_call_order_is_lifo(self) -> None:
        """Multiple callbacks are executed in LIFO (last registered first) order."""
        self.name = 'test_callbacks_call_order_is_lifo'
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[3])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[2])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[1])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback_unauthorized_append(self) -> None:
        """Registering a callback with append=False raises when a handler already exists."""
        self.name = 'test_callback_unauthorized_append'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        with pytest.raises(exceptions.MultipleSignalHandlersError):
            signals.register_callback(
                signal.SIGTERM,
                self.set_flag_callback,
                append=False,
                args=[None],
            )
        os.kill(os.getpid(), signal.SIGTERM)

    def test_handler_appends_existing_function_handler(self) -> None:
        """A pre-existing function handler is preserved when register_handler is called."""

        def existing_handler(signum, frame):  # pylint:disable=unused-argument
            pass

        signal.signal(signal.SIGTERM, existing_handler)
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        assert existing_handler in signals.handlers_by_signal[signal.SIGTERM]
        self.name = 'test_handler_appends_existing_function_handler'
        os.kill(os.getpid(), signal.SIGTERM)

    def test_handler_error_propagation(self) -> None:
        """Exceptions from signal handlers are collected and re-raised as RuntimeError."""

        def failing_handler(signum, frame):  # pylint:disable=unused-argument
            raise ValueError('handler failed')

        signals.register_handler(signal.SIGTERM, failing_handler, reset=True)
        with pytest.raises(RuntimeError):
            os.kill(os.getpid(), signal.SIGTERM)
