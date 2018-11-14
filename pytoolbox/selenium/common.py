# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

from . import exceptions

_all = module.All(globals())


class FindMixin(object):

    def clean_elements(self, elements, criteria, force_list=False, fail=True):
        if elements:
            return elements if force_list or len(elements) > 1 else elements[0]
        if fail:
            raise exceptions.NoSuchElementException(criteria)

    def find_css(self, css_selector, *args, **kwargs):
        return self.clean_elements(
            self.find_elements_by_css_selector(css_selector), css_selector, *args, **kwargs)

    def find_id(self, element_id, *args, **kwargs):
        return self.find_css('#{0}'.format(element_id), *args, **kwargs)

    def find_name(self, element_name, *args, **kwargs):
        return self.find_css('[name={0}]'.format(element_name), *args, **kwargs)

    def find_xpath(self, xpath, *args, **kwargs):
        return self.clean_elements(self.find_elements_by_xpath(xpath), xpath, *args, **kwargs)


__all__ = _all.diff(globals())
