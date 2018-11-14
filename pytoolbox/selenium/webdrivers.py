# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from selenium import webdriver

from pytoolbox import module

from . import common, select, webelements

_all = module.All(globals())


class Firefox(common.FindMixin, webdriver.Firefox):

    web_element_classes = {
        'default': webelements.WebElement,
        'select': select.Select
    }

    def _wrap_value(self, value):
        if isinstance(value, tuple(self.web_element_classes.itervalues())):
            return {'ELEMENT': value.id, 'element-6066-11e4-a52e-4f735466cecf': value.id}
        return super()._wrap_value(value)

    def create_web_element(self, element_id):
        element = self.web_element_classes['default'](self, element_id)
        tag_name = getattr(element, 'tag_name', 'default')
        cls = self.web_element_classes.get(tag_name)
        return cls(element) if cls else element


__all__ = _all.diff(globals())
