"""
Web element mixin for Bootstrap Switch components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pytoolbox.compat import override
from pytoolbox.selenium import Keys, common

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

# The mixin completes a WebElement, whose API it calls; naming the base under TYPE_CHECKING states
# that requirement for the checker only.
_WebElementMixin = WebElement if TYPE_CHECKING else object

__all__ = ['BootstrapSwitchMixin']


class BootstrapSwitchMixin(common.FindMixin, _WebElementMixin):
    """Mixin for interacting with Bootstrap Switch toggle elements."""

    component = 'bootstrapSwitch'
    key_map: ClassVar[dict[bool, str]] = {True: Keys.RIGHT, False: Keys.LEFT}

    @staticmethod
    def clean_value(value: str | bool) -> bool:
        """Normalize the switch value to a boolean."""
        return {'on': True, 'off': False, True: True, False: False}[value]

    @override
    def send_keys(self, *value: str | bool) -> None:
        """Translate boolean values to arrow key presses."""
        keys = [self.key_map[v] if isinstance(v, bool) else v for v in value]
        return super().send_keys(*keys)
