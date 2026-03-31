"""
Signal handling with support for multiple handlers per signal.
"""

from __future__ import annotations

import collections
import inspect
import signal
from collections.abc import Callable
from types import FrameType

from . import exceptions

__all__ = ['handlers_by_signal', 'propagate_handler', 'register_handler', 'register_callback']

handlers_by_signal: collections.defaultdict[int, list[Callable]] = collections.defaultdict(list)


def propagate_handler(signum: int, frame: FrameType | None) -> None:
    """Call all registered handlers for a signal in reverse order."""
    errors = {}
    for handler in reversed(handlers_by_signal[signum]):
        try:
            handler(signum, frame)
        except Exception as exc:  # pylint:disable=broad-except
            errors[handler] = exc
    if errors:
        raise RuntimeError(errors)


def register_handler(
    signum: int,
    handler: Callable,
    *,
    append: bool = True,
    reset: bool = False,
) -> None:
    """Register a signal handler, optionally appending to existing ones."""
    old_handler = signal.getsignal(signum)
    signal.signal(signum, propagate_handler)
    if inspect.isfunction(old_handler) and old_handler is not propagate_handler:
        handlers_by_signal[signum].append(old_handler)
    handlers = handlers_by_signal[signum]
    if not append and handlers:
        raise exceptions.MultipleSignalHandlersError(signum=signum, handlers=handlers)
    if reset:
        try:
            handlers.clear()
        except AttributeError:
            # < Python 3.3
            del handlers[:]
    handlers.append(handler)


def register_callback(
    signum: int,
    callback: Callable,
    *,
    append: bool = True,
    reset: bool = False,
    args: list | None = None,
    kwargs: dict | None = None,
) -> None:
    """Register a callback as a signal handler, wrapping it to ignore ``signum`` and ``frame``."""
    return register_handler(
        signum,
        lambda s, f: callback(*(args or []), **(kwargs or {})),
        append=append,
        reset=reset,
    )
