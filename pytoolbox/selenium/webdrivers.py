"""
Custom Selenium WebDriver subclasses with element specialization.
"""

from __future__ import annotations

from typing import Any

from selenium import webdriver

from . import common, select, webelements

__all__ = ['Firefox']


class Firefox(common.FindMixin, webdriver.Firefox):
    """Firefox WebDriver that creates specialized web elements."""

    web_element_classes = {
        'default': webelements.WebElement,
        'select': select.Select,
    }

    def _wrap_value(self, value: Any) -> Any:
        if isinstance(value, tuple(self.web_element_classes.values())):
            return {'ELEMENT': value.id, 'element-6066-11e4-a52e-4f735466cecf': value.id}
        return super()._wrap_value(value)

    def create_web_element(self, element_id: str) -> webelements.WebElement:
        """Create a web element, specializing it based on ``data-component``."""
        element = self.web_element_classes['default'](self, element_id)
        tag_name = getattr(element, 'tag_name', 'default')
        cls = self.web_element_classes.get(tag_name)
        return cls(element) if cls else element

    # pylint:disable=useless-parent-delegation

    def delete_downloadable_files(self, *args, **kwargs) -> Any:
        """Delete downloadable files from the remote browser."""
        return super().delete_downloadable_files(*args, **kwargs)

    def download_file(self, *args, **kwargs) -> Any:
        """Download a file from the remote browser."""
        return super().download_file(*args, **kwargs)

    def get_downloadable_files(self, *args, **kwargs) -> Any:
        """Return the list of downloadable files from the remote browser."""
        return super().get_downloadable_files(*args, **kwargs)
