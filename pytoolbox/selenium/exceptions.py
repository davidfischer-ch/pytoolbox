from __future__ import annotations

from selenium.common import exceptions

# Replace the infamous "from selenium.common.exceptions import *" :)
things = {k: v for k, v in exceptions.__dict__.items() if k[0] != '_'}
__all__ = sorted(list(things.keys()) + ['NoSuchSpecializedElementException'])
assert 'NoSuchSpecializedElementException' not in things

globals().update(things)


class NoSuchSpecializedElementException(exceptions.NoSuchElementException):
    pass
