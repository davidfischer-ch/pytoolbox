from __future__ import annotations

from typing import Any

__all__ = ['All']


class All(object):  # pylint:disable=too-few-public-methods

    def __init__(self, globals_: dict[str, Any]) -> None:
        self.init_keys: set[str] = set(globals_.keys())

    def diff(self, globals_: dict[str, Any]) -> list[str]:
        new_keys = set(globals_.keys()) - self.init_keys
        return [k for k in new_keys if k[0] != '_']
