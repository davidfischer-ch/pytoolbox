# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from selenium.webdriver.remote import webelement

from pytoolbox import module
from pytoolbox.selenium import common, exceptions

_all = module.All(globals())


class WebElement(common.FindMixin, webelement.WebElement):

    def __init__(self, *args, **kwargs):
        super(WebElement, self).__init__(*args, **kwargs)
        self._specialize()

    def clean_value(self, value):
        return value

    def get_attribute(self, name):
        value = super(WebElement, self).get_attribute(name)
        return self.clean_value(value) if name == 'value' else value

    def _specialize(self):
        component = self.get_attribute('data-component')
        if component:
            try:
                self.__class__ = next(
                    c for c in type(self).__subclasses__() if c.component == component)
            except StopIteration:
                self._specialize_default(component)

    def _specialize_default(self, component):
        raise exceptions.NoSuchSpecializedElementException(
            'Unable to find a class implementing the component {0}.'.format(component)
        )


__all__ = _all.diff(globals())
