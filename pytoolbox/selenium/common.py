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

from . import exceptions
from .. import module

_all = module.All(globals())


class FindMixin(object):

    def clean_elements(self, elements, criteria, force_list=False, fail=True):
        if elements:
            return elements if force_list or len(elements) > 1 else elements[0]
        if fail:
            raise exceptions.NoSuchElementException(criteria)

    def find_css(self, css_selector, *args, **kwargs):
        return self.clean_elements(self.find_elements_by_css_selector(css_selector), css_selector, *args, **kwargs)

    def find_id(self, element_id, *args, **kwargs):
        return self.find_css('#{0}'.format(element_id), *args, **kwargs)

    def find_name(self, element_name, *args, **kwargs):
        return self.find_css('[name={0}]'.format(element_name), *args, **kwargs)

    def find_xpath(self, xpath, *args, **kwargs):
        return self.clean_elements(self.find_elements_by_xpath(xpath), xpath, *args, **kwargs)

__all__ = _all.diff(globals())
