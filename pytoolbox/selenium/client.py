"""
Selenium live test client for interacting with a running server.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import ui

from . import common, exceptions, webdrivers

__all__ = ['LiveClient']


class LiveClient(common.FindMixin):
    """High-level Selenium client for live server testing."""

    web_driver_class = webdrivers.Firefox

    def __init__(self, live_server_url: str, web_driver_class: type | None = None) -> None:
        self.live_server_url = live_server_url
        if web_driver_class:
            self.web_driver_class = web_driver_class
        self.web_driver = self.web_driver_class()
        self._css_prefix = ''

    @property
    def css_prefix(self) -> str:
        """Return the CSS selector prefix prepended to all queries."""
        return self._css_prefix

    @css_prefix.setter
    def css_prefix(self, value: str) -> None:
        """Set the CSS selector prefix, raising if one is already active."""
        assert not value or not self._css_prefix, self._css_prefix
        self._css_prefix = value

    def find_css(
            self,
            css_selector: str,
            *,
            prefix: bool = True,
            force_list: bool = False,
            fail: bool = True) -> Any:
        """Shortcut to find elements by CSS. Returns either a list or singleton."""
        if prefix and self.css_prefix:
            css_selector = f'{self.css_prefix} {css_selector}'
        return self.web_driver.find_css(css_selector, force_list=force_list, fail=fail)

    def find_xpath(self, xpath: str, *, force_list: bool = False, fail: bool = True) -> Any:
        """Find elements by XPath expression."""
        return self.web_driver.find_xpath(xpath, force_list=force_list, fail=fail)

    def get(self, url: str, *, data: Any = None) -> Any:
        """Navigate to a URL relative to the live server."""
        assert data is None
        url = urljoin(self.live_server_url, url) if '://' not in url else url
        response = type('Response', (object, ), self.web_driver.execute(Command.GET, {'url': url}))
        response.status_code = 200 if self.web_driver.current_url == url else 404
        return response

    def quit(self) -> None:
        """Quit the underlying web driver."""
        return self.web_driver.quit()

    def set_element(self, name: str, value: Any, *, clear: bool | None = None) -> None:
        """Set the properties of an element. Works with both WebElement and Select."""
        element = self.find_name(name)
        if clear is None:
            clear = element.is_displayed()
        if isinstance(element, self.web_driver.web_element_classes['select']):
            return element.select_by_value(value)
        if clear:
            element.clear()
        return element.send_keys(value)

    def submit(self) -> None:
        """Click the primary submit button of the current form."""
        return self.find_css('form button.btn-primary[type="submit"]').click()

    def wait_for_css(
            self,
            css_selector: str = '',
            *,
            inverse: bool = False,
            prefix: bool = True,
            timeout: int = 5,
            fail: bool = True) -> bool | None:
        """Wait until a CSS selector matches (or stops matching if *inverse*)."""
        try:
            def wait_func(driver: Any) -> bool:  # pylint:disable=unused-argument
                return bool(self.find_css(css_selector, prefix=prefix, fail=False)) ^ inverse
            return ui.WebDriverWait(self.web_driver, timeout).until(wait_func)
        except exceptions.TimeoutException:  # pylint:disable=no-member
            if fail:
                raise
        return None

    def wait_for_id(
            self,
            element_id: str,
            *,
            inverse: bool = False,
            prefix: bool = True,
            timeout: int = 5,
            fail: bool = True) -> bool | None:
        """Wait until an element with the given ID is present."""
        return self.wait_for_css(
            f'#{element_id}',
            inverse=inverse,
            prefix=prefix,
            timeout=timeout,
            fail=fail)

    def wait_for_name(
            self,
            element_name: str,
            *,
            inverse: bool = False,
            prefix: bool = True,
            timeout: int = 5,
            fail: bool = True) -> bool | None:
        """Wait until an element with the given name attribute is present."""
        return self.wait_for_css(
            f'[name="{element_name}"]',
            inverse=inverse,
            prefix=prefix,
            timeout=timeout,
            fail=fail)
