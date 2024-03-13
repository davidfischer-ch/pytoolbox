from __future__ import annotations

from selenium.webdriver.remote import webelement

from pytoolbox.selenium import common, exceptions

__all__ = ['WebElement']


class WebElement(common.FindMixin, webelement.WebElement):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._specialize()

    @staticmethod
    def clean_value(value):
        return value

    def get_attribute(self, name):
        value = super().get_attribute(name)
        return self.clean_value(value) if name == 'value' else value

    def _specialize(self):
        if component := self.get_attribute('data-component'):
            try:
                self.__class__ = next(  # pylint: disable=invalid-class-object
                    c for c in type(self).__subclasses__() if c.component == component)
            except StopIteration:
                self._specialize_default(component)

    @staticmethod
    def _specialize_default(component):
        raise exceptions.NoSuchSpecializedElementException(
            f'Unable to find a class implementing the component {component}.')
