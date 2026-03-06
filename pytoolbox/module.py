"""
Utilities for building a module's ``__all__`` list automatically.
"""
from __future__ import annotations

from typing import Any

__all__ = ['All']


class All(object):  # pylint:disable=too-few-public-methods
    """Track new public names added to a module's globals for ``__all__``."""

    def __init__(self, globals_: dict[str, Any]) -> None:
        self.init_keys: set[str] = set(globals_.keys())

    def diff(self, globals_: dict[str, Any]) -> list[str]:
        """Return public names added since this instance was created."""
        new_keys = set(globals_.keys()) - self.init_keys
        return [k for k in new_keys if k[0] != '_']
