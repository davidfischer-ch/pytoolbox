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

from selenium.webdriver.remote import webelement

from .. import common, exceptions
from ... import module

_all = module.All(globals())


class WebElement(common.FindMixin, webelement.WebElement):

    def __init__(self, *args, **kwargs):
        super(WebElement, self).__init__(*args, **kwargs)
        self._specialize()

    def clean_value(self, value):
        return value

    def get_attribute(self, name):
        value = super(WebElement, self).get_attribute(name)
        return self.clean_value(value) if name == 'value' else value

    def _specialize(self):
        component = self.get_attribute('data-component')
        if component:
            try:
                self.__class__ = next(c for c in type(self).__subclasses__() if c.component == component)
            except StopIteration:
                self._specialize_default(component)

    def _specialize_default(self, component):
        raise exceptions.NoSuchSpecializedElementException(
            'Unable to find a class implementing the component {0}.'.format(component)
        )

__all__ = _all.diff(globals())
