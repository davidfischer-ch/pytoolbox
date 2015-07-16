# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

from . import base
from .. import Keys
from ... import module

_all = module.All(globals())


class BootsrapSlider(base.WebElement):

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
