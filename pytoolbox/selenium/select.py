from __future__ import annotations

from selenium.webdriver.support import select

__all__ = ['Select']


class Select(select.Select):
    """A Select with the attributes of the WebElement."""

    def __getattr__(self, name):
        return getattr(self._el, name)
