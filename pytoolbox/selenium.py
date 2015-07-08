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

import functools
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import ui
from selenium.webdriver.support.select import Select
from urllib.parse import urljoin

from . import module

_all = module.All(globals())

SPECIALIZE_ELEMENT_MAP = {'select': Select}


def specialize_elements(f, specialize_map=SPECIALIZE_ELEMENT_MAP):
    @functools.wraps(f)
    def _specialize_elements(*args, **kwargs):
        elements = f(*args, **kwargs)
        if isinstance(elements, list):
            return [specialize_map.get(getattr(e, 'tag_name', None), lambda e: e)(e) for e in elements]
        return specialize_map.get(getattr(elements, 'tag_name', None), lambda e: e)(elements)
    return _specialize_elements


class LiveClient(object):

    web_driver_class = Firefox

    def __init__(self, live_server_url, web_driver_class=None):
        self.live_server_url = live_server_url
        if web_driver_class:
            self.web_driver_class = web_driver_class
        self.web_driver = self.web_driver_class()
        self._css_prefix = ''

    @property
    def css_prefix(self):
        return self._css_prefix

    @css_prefix.setter
    def css_prefix(self, value):
        assert not value or not self._css_prefix, self._css_prefix
        self._css_prefix = value

    @specialize_elements
    def find_css(self, css_selector, prefix=True):
        """Shortcut to find elements by CSS. Returns either a list or singleton."""
        if prefix and self.css_prefix:
            css_selector = '{0.css_prefix} {1}'.format(self, css_selector)
        elements = self.web_driver.find_elements_by_css_selector(css_selector)
        if not elements:
            raise NoSuchElementException(css_selector)
        return elements[0] if len(elements) == 1 else elements

    @specialize_elements
    def find_id(self, element_id, prefix=True):
        return self.find_css('#{0}'.format(element_id), prefix)

    @specialize_elements
    def find_name(self, element_name, prefix=True):
        return self.find_css('[name="{0}"]'.format(element_name), prefix)

    def get(self, url, data=None):
        assert data is None
        url = urljoin(self.live_server_url, url) if '://' not in url else url
        response = type('Response', (object, ), self.web_driver.execute(Command.GET, {'url': url}))
        response.status_code = 200 if self.web_driver.current_url == url else 404
        return response

    def quit(self):
        return self.web_driver.quit()

    def submit(self):
        return self.find_css('form button.btn-primary[type="submit"]').click()

    def wait_for_css(self, css_selector='', prefix=True, timeout=5):
        return ui.WebDriverWait(self.web_driver, timeout).until(lambda driver: self.find_css(css_selector, prefix))

__all__ = _all.diff(globals())
