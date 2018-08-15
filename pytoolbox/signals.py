# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, inspect, signal

from . import exceptions, module

_all = module.All(globals())

handlers_by_signal = collections.defaultdict(list)


def propagate_handler(signum, frame):
    errors = {}
    for handler in reversed(handlers_by_signal[signum]):
        try:
            handler(signum, frame)
        except Exception as e:
            errors[handler] = e
    if errors:
        raise RuntimeError(errors)


def register_handler(signum, handler, append=True, reset=False):
    old_handler = signal.getsignal(signum)
    signal.signal(signum, propagate_handler)
    if inspect.isfunction(old_handler) and old_handler != propagate_handler:
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


def register_callback(signum, callback, append=True, reset=False, args=None, kwargs=None):
    return register_handler(
        signum, lambda s, f: callback(*(args or []), **(kwargs or {})), append, reset)


__all__ = _all.diff(globals())
