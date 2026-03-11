# pylint:disable=no-member
"""
Common mixins for Selenium element lookup.
"""
from __future__ import annotations

from typing import Any

from . import exceptions

__all__ = ['FindMixin']


class FindMixin:
    """Mixin providing shortcut methods for finding web elements."""

    @staticmethod
    def clean_elements(
            elements: list,
            criteria: str,
            *,
            force_list: bool = False,
            fail: bool = True
    ) -> Any:
        """Return a single element, a list, or raise if none found."""
        if elements:
            return elements if force_list or len(elements) > 1 else elements[0]
        if fail:
            raise exceptions.NoSuchElementException(criteria)
        return None

    def find_css(
            self,
            css_selector: str,
            *,
            prefix: bool = True,
            force_list: bool = False,
            fail: bool = True
    ) -> Any:
        """Find elements by CSS selector."""
        assert prefix  # Not implemented
        elements = self.find_elements_by_css_selector(css_selector)
        return self.clean_elements(elements, css_selector, force_list=force_list, fail=fail)

    def find_id(
            self,
            element_id: str,
            *,
            prefix: bool = True,
            force_list: bool = False,
            fail: bool = True
    ) -> Any:
        """Find elements by their HTML ``id`` attribute."""
        return self.find_css(f'#{element_id}', prefix=prefix, force_list=force_list, fail=fail)

    def find_name(
            self,
            element_name: str,
            *,
            prefix: bool = True,
            force_list: bool = False,
            fail: bool = True
    ) -> Any:
        """Find elements by their ``name`` attribute."""
        return self.find_css(
            f'[name={element_name}]',
            prefix=prefix,
            force_list=force_list,
            fail=fail)

    def find_xpath(self, xpath: str, *, force_list: bool = False, fail: bool = True) -> Any:
        """Find elements by XPath expression."""
        elements = self.find_elements_by_xpath(xpath)
        return self.clean_elements(elements, xpath, force_list=force_list, fail=fail)
