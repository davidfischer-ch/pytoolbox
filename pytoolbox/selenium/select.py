"""
Extended :class:`~selenium.webdriver.support.select.Select` with element attribute delegation.
"""
from __future__ import annotations

from typing import Any

from selenium.webdriver.support import select

__all__ = ['Select']


class Select(select.Select):
    """A Select with the attributes of the WebElement."""

    def __getattr__(self, name: str) -> Any:
        return getattr(self._el, name)
