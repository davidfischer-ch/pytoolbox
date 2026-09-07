"""
Web element mixin for Bootstrap Slider components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytoolbox.compat import override
from pytoolbox.selenium import Keys, common

if TYPE_CHECKING:
    from selenium.webdriver.remote.webelement import WebElement

# The mixin completes a WebElement, whose API it calls; naming the base under TYPE_CHECKING states
# that requirement for the checker only.
_WebElementMixin = WebElement if TYPE_CHECKING else object

__all__ = ['BootstrapSliderMixin']


class BootstrapSliderMixin(common.FindMixin, _WebElementMixin):
    """Mixin for interacting with Bootstrap Slider elements."""

    component = 'bootstrapSlider'

    @staticmethod
    def clean_value(value: str | int) -> int:
        """Coerce the slider value to an integer."""
        return int(value)

    @override
    def clear(self) -> None:
        """Clear the slider value (not yet implemented)."""
        # TODO something to do?

    @override
    def send_keys(self, *value: str | int) -> None:
        """Move the slider handle to the target value using arrow keys."""
        if len(value) == 1:
            target = self.clean_value(value[0])
            slider_xpath = "..//*[contains(concat(' ', @class, ' '), ' slider-handle ')]"
            slider = next(e for e in self.find_xpath(slider_xpath) if e.is_displayed())
            # TODO detect step and make a loop to reach the target value
            delta = target - self.clean_value(self.get_attribute('value') or 0)
            if delta > 0:
                slider.send_keys([Keys.RIGHT] * delta)
            elif delta < 0:
                slider.send_keys([Keys.LEFT] * -delta)
            return
        raise NotImplementedError(f'Sending {value} not implemented.')
