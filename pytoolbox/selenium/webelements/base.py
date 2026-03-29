"""
Base :class:`WebElement` with automatic component specialization.
"""

from __future__ import annotations

from typing import Any

from selenium.webdriver.remote import webelement

from pytoolbox.selenium import common, exceptions

__all__ = ['WebElement']


class WebElement(common.FindMixin, webelement.WebElement):
    """A web element that specializes itself based on ``data-component``."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._specialize()

    @staticmethod
    def clean_value(value: Any) -> Any:
        """Return the value as-is (subclasses may override to coerce types)."""
        return value

    def get_attribute(self, name: str) -> Any:
        """Return an attribute, applying :meth:`clean_value` for ``value``."""
        value = super().get_attribute(name)
        return self.clean_value(value) if name == 'value' else value

    def _specialize(self) -> None:
        if component := self.get_attribute('data-component'):
            try:
                self.__class__ = next(  # pylint: disable=invalid-class-object
                    c for c in type(self).__subclasses__() if c.component == component
                )
            except StopIteration:
                self._specialize_default(component)

    @staticmethod
    def _specialize_default(component: str) -> None:
        raise exceptions.NoSuchSpecializedElementException(
            f'Unable to find a class implementing the component {component}.',
        )
