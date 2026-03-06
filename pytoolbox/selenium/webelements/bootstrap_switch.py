# pylint:disable=no-member
"""
Web element mixin for Bootstrap Switch components.
"""
from __future__ import annotations

from pytoolbox.selenium import common, Keys

__all__ = ['BootstrapSwitchMixin']


class BootstrapSwitchMixin(common.FindMixin):
    """Mixin for interacting with Bootstrap Switch toggle elements."""

    component = 'bootstrapSwitch'
    key_map = {True: Keys.RIGHT, False: Keys.LEFT}

    @staticmethod
    def clean_value(value: str | bool) -> bool:
        """Normalize the switch value to a boolean."""
        return {'on': True, 'off': False, True: True, False: False}[value]

    def send_keys(self, *value: str | bool) -> None:
        """Translate boolean values to arrow key presses."""
        return super().send_keys(*[self.key_map.get(v, v) for v in value])
