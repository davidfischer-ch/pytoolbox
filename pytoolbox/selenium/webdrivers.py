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

from selenium import webdriver

from . import common, select, webelements
from .. import module

_all = module.All(globals())


class Firefox(common.FindMixin, webdriver.Firefox):

    web_element_classes = {
        'default': webelements.WebElement,
        'select': select.Select
    }

    def _wrap_value(self, value):
        if isinstance(value, tuple(self.web_element_classes.values())):
            return {'ELEMENT': value.id, 'element-6066-11e4-a52e-4f735466cecf': value.id}
        return super()._wrap_value(value)

    def create_web_element(self, element_id):
        element = self.web_element_classes['default'](self, element_id)
        tag_name = getattr(element, 'tag_name', 'default')
        cls = self.web_element_classes.get(tag_name)
        return cls(element) if cls else element


__all__ = _all.diff(globals())
