# pylint:disable=no-member
from __future__ import annotations


from . import exceptions

__all__ = ['FindMixin']


class FindMixin(object):

    @staticmethod
    def clean_elements(elements, criteria, *, force_list=False, fail=True):
        if elements:
            return elements if force_list or len(elements) > 1 else elements[0]
        if fail:
            raise exceptions.NoSuchElementException(criteria)
        return None

    def find_css(self, css_selector, *, prefix=True, force_list=False, fail=True):
        assert prefix  # Not implemented
        elements = self.find_elements_by_css_selector(css_selector)
        return self.clean_elements(elements, css_selector, force_list=force_list, fail=fail)

    def find_id(self, element_id, *, prefix=True, force_list=False, fail=True):
        return self.find_css(f'#{element_id}', prefix=prefix, force_list=force_list, fail=fail)

    def find_name(self, element_name, *, prefix=True, force_list=False, fail=True):
        return self.find_css(
            f'[name={element_name}]',
            prefix=prefix,
            force_list=force_list,
            fail=fail)

    def find_xpath(self, xpath, *, force_list=False, fail=True):
        elements = self.find_elements_by_xpath(xpath)
        return self.clean_elements(elements, xpath, force_list=force_list, fail=fail)
