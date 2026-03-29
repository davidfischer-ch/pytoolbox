# pylint:disable=no-member
"""
Web element mixin for Bootstrap Slider components.
"""

from __future__ import annotations

from pytoolbox.selenium import Keys, common

__all__ = ['BootstrapSliderMixin']


class BootstrapSliderMixin(common.FindMixin):
    """Mixin for interacting with Bootstrap Slider elements."""

    component = 'bootstrapSlider'

    @staticmethod
    def clean_value(value: str | int) -> int:
        """Coerce the slider value to an integer."""
        return int(value)

    def clear(self) -> None:
        """Clear the slider value (not yet implemented)."""
        pass  # TODO something to do?  # pylint:disable=unnecessary-pass

    def send_keys(self, *value: str | int) -> None:
        """Move the slider handle to the target value using arrow keys."""
        if len(value) == 1:
            value = self.clean_value(value[0])
            slider_xpath = "..//*[contains(concat(' ', @class, ' '), ' slider-handle ')]"
            slider = next(e for e in self.find_xpath(slider_xpath) if e.is_displayed())
            # TODO detect step and make a loop to reach the target value
            delta = value - self.get_attribute('value')
            if delta > 0:
                slider.send_keys([Keys.RIGHT] * delta)
            elif delta < 0:
                slider.send_keys([Keys.LEFT] * -delta)
            return
        raise NotImplementedError(f'Sending {value} not implemented.')
