# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from urlparse import urljoin

from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import ui

from pytoolbox import module

from . import common, exceptions, webdrivers

_all = module.All(globals())


class LiveClient(common.FindMixin):

    web_driver_class = webdrivers.Firefox

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

    def find_css(self, css_selector, prefix=True, force_list=False, fail=True):
        """Shortcut to find elements by CSS. Returns either a list or singleton."""
        if prefix and self.css_prefix:
            css_selector = '{0.css_prefix} {1}'.format(self, css_selector)
        return self.web_driver.find_css(css_selector, force_list=force_list, fail=fail)

    def find_xpath(self, xpath, force_list=False, fail=True):
        return self.web_driver.find_xpath(xpath, force_list=force_list, fail=fail)

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
        if clear is None:
            clear = element.is_displayed()
        if isinstance(element, self.web_driver.web_element_classes['select']):
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
                lambda driver: bool(self.find_css(css_selector, prefix, fail=False)) ^ inverse
            )
        except exceptions.TimeoutException:
            if fail:
                raise

    def wait_for_id(self, element_id, inverse=False, prefix=True, timeout=5, fail=True):
        return self.wait_for_css('#{0}'.format(element_id), inverse, prefix, timeout, fail)

    def wait_for_name(self, element_name, inverse=False, prefix=True, timeout=5, fail=True):
        return self.wait_for_css(
            '[name="{0}"]'.format(element_name), inverse, prefix, timeout, fail)


__all__ = _all.diff(globals())
