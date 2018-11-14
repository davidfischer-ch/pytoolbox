# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module
from pytoolbox.selenium import Keys

_all = module.All(globals())


class BootstrapSliderMixin(object):

    component = 'bootstrapSlider'

    def clean_value(self, value):
        return int(value)

    def clear(self):
        pass  # FIXME something to do?

    def send_keys(self, *value):
        if len(value) == 1:
            value = self.clean_value(value[0])
            slider_xpath = "..//*[contains(concat(' ', @class, ' '), ' slider-handle ')]"
            slider = next(e for e in self.find_xpath(slider_xpath) if e.is_displayed())
            # FIXME detect step and make a loop to reach the target value
            delta = value - self.get_attribute('value')
            if delta > 0:
                slider.send_keys([Keys.RIGHT] * delta)
            elif delta < 0:
                slider.send_keys([Keys.LEFT] * -delta)
            return
        raise NotImplementedError('Sending {0} not implemented.'.format(value))


__all__ = _all.diff(globals())
