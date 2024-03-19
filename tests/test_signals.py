from __future__ import annotations

import os
import signal
import unittest

import pytest
from pytoolbox import exceptions, signals


# TODO Convert to simple pytest tests
class TestSignals(unittest.TestCase):

    def append_list_callback(self, number) -> None:
        self.flag = True
        self.list.append(number)

    def raise_handler(self, signum, frame) -> None:
        raise AssertionError

    def set_flag_handler(self, signum, frame) -> None:  # pylint:disable=unused-argument
        self.flag = True

    def set_flag_callback(self, *args, **kwargs) -> None:
        assert args == (None, )
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
        self.name = 'test_handler'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_handler_reset(self) -> None:
        self.name = 'test_handler_reset'
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler)
        signals.register_handler(signal.SIGTERM, self.raise_handler, reset=True)
        signals.register_handler(signal.SIGTERM, self.set_flag_handler, reset=True)
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback(self) -> None:
        self.name = 'test_callback'
        signals.register_callback(signal.SIGTERM, self.set_flag_callback, args=[None])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callbacks_call_order_is_lifo(self) -> None:
        self.name = 'test_callbacks_call_order_is_lifo'
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[3])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[2])
        signals.register_callback(signal.SIGTERM, self.append_list_callback, args=[1])
        os.kill(os.getpid(), signal.SIGTERM)

    def test_callback_unauthorized_append(self) -> None:
        self.name = 'test_callback_unauthorized_append'
        signals.register_handler(signal.SIGTERM, self.set_flag_handler)
        with pytest.raises(exceptions.MultipleSignalHandlersError):
            signals.register_callback(
                signal.SIGTERM, self.set_flag_callback, append=False, args=[None])
        os.kill(os.getpid(), signal.SIGTERM)
