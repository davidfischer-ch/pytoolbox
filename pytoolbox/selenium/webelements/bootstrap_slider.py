# pylint:disable=no-member
from __future__ import annotations


from pytoolbox.selenium import common, Keys

__all__ = ['BootstrapSliderMixin']


class BootstrapSliderMixin(common.FindMixin):

    component = 'bootstrapSlider'

    @staticmethod
    def clean_value(value):
        return int(value)

    def clear(self):
        pass  # TODO something to do?

    def send_keys(self, *value):
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
