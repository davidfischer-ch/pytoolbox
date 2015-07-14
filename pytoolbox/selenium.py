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
from selenium.webdriver import Firefox
from selenium.webdriver.common import keys
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import select, ui
from urlparse import urljoin

from . import module

_all = module.All(globals())

# Integrate some utility modules and classes
from selenium.common import exceptions
Keys = keys.Keys


class Select(select.Select):
    """A Select with the attributes of the WebElement."""

    def __getattr__(self, name):
        return getattr(self._el, name)

SPECIALIZE_ELEMENT_MAP = {'select': Select, 'default': lambda e: e}


def specialize_elements(f, specialize_map=SPECIALIZE_ELEMENT_MAP):
    @functools.wraps(f)
    def _specialize_elements(*args, **kwargs):
        elements, default = f(*args, **kwargs), specialize_map['default']
        if isinstance(elements, list):
            return [specialize_map.get(getattr(e, 'tag_name', 'default'), default)(e) for e in elements]
        return specialize_map.get(getattr(elements, 'tag_name', 'default'), default)(elements)
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
    def find_css(self, css_selector, prefix=True, fail=True):
        """Shortcut to find elements by CSS. Returns either a list or singleton."""
        if prefix and self.css_prefix:
            css_selector = '{0.css_prefix} {1}'.format(self, css_selector)
        elements = self.web_driver.find_elements_by_css_selector(css_selector)
        if elements:
            return elements[0] if len(elements) == 1 else elements
        if fail:
            raise exceptions.NoSuchElementException(css_selector)

    def find_id(self, element_id, prefix=True, fail=True):
        return self.find_css('#{0}'.format(element_id), prefix)

    def find_name(self, element_name, prefix=True, fail=True):
        return self.find_css('[name="{0}"]'.format(element_name), prefix)

    def get(self, url, data=None):
        assert data is None
        url = urljoin(self.live_server_url, url) if '://' not in url else url
        response = type('Response', (object, ), self.web_driver.execute(Command.GET, {'url': url}))
        response.status_code = 200 if self.web_driver.current_url == url else 404
        return response

    def quit(self):
        return self.web_driver.quit()

    def set_element(self, name, value, clear=None):
        """Set the properties of an element. Works with both WebElement and Select."""
        element = self.find_name(name)
        if isinstance(value, bool):
            if clear:
                raise ValueError('You cannot clear a boolean element.')
            # FIXME this is designed to work bootstrapSwitch and not regular check-boxes
            value = Keys.RIGHT if value else Keys.LEFT
        elif clear is None:
            clear = True
        if isinstance(element, Select):
            return element.select_by_value(value)
        else:
            if clear:
                element.clear()
            return element.send_keys(value)
        raise NotImplementedError

    def submit(self):
        return self.find_css('form button.btn-primary[type="submit"]').click()

    def wait_for_css(self, css_selector='', inverse=False, prefix=True, timeout=5, fail=True):
        try:
            return ui.WebDriverWait(self.web_driver, timeout).until(
                lambda driver: bool(self.find_css(css_selector, prefix)) ^ inverse
            )
        except exceptions.TimeoutException:
            if fail:
                raise

    def wait_for_id(self, element_id, inverse=False, prefix=True, timeout=5, fail=True):
        return self.wait_for_css('#{0}'.format(element_id), inverse, prefix, timeout, fail)

    def wait_for_name(self, element_name, inverse=False, prefix=True, timeout=5, fail=True):
        return self.wait_for_css('[name="{0}"]'.format(element_name), inverse, prefix, timeout, fail)


class LiveTestCaseMixin(object):

    live_client_class = LiveClient

    def setUp(self):
        """Call super's setUp and instantiate a live test client, only once."""
        super(LiveTestCaseMixin, self).setUp()
        if not hasattr(self.__class__, 'client'):
            self.__class__.client = self.live_client_class(self.live_server_url)
        self.client = self.__class__.client

    @classmethod
    def tearDownClass(cls):
        """Quit the live-test client and call super's tearDownClass."""
        cls.client.quit()
        super(LiveTestCaseMixin, cls).tearDownClass()

    # Asserts

    def assertElementEqual(self, name, value, enabled=True):
        """Check the properties of an element. Works with both WebElement and Select."""
        self.assertElementIsEnabled(name) if enabled else self.assertElementIsDisabled(name)
        if isinstance(value, bool):
            # FIXME this is designed to work bootstrapSwitch and not regular check-boxes
            value = 'on' if value else 'off'
        element = self.client.find_name(name)
        method = self.assertSelectOptions if isinstance(element, Select) else self.assertElementValue
        method(name, value)

    def assertElementIsDisabled(self, name, *args, **kwargs):
        self.assertFalse(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsEnabled(self, name, *args, **kwargs):
        self.assertTrue(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsReadOnly(self, name):
        self.assertIsNotNone(self.client.find_name(name).get_attribute('readonly'))

    def assertElementValue(self, name, value, *args, **kwargs):
        operator = kwargs.pop('operator', lambda x: x)
        self.assertEqual(operator(self.client.find_name(name).get_attribute('value')), value, *args, **kwargs)

    def assertSelectOptions(self, name, texts, *args, **kwargs):
        self.assertListEqual(sorted(o.text for o in self.client.find_name(name).all_selected_options),
                             sorted([texts] if isinstance(texts, str) else texts), *args, **kwargs)


__all__ = _all.diff(globals())
