from . import exceptions

__all__ = ['FindMixin']


class FindMixin(object):

    def clean_elements(self, elements, criteria, force_list=False, fail=True):
        if elements:
            return elements if force_list or len(elements) > 1 else elements[0]
        if fail:
            raise exceptions.NoSuchElementException(criteria)

    def find_css(self, css_selector, *args, **kwargs):
        elements = self.find_elements_by_css_selector(css_selector)
        return self.clean_elements(elements, css_selector, *args, **kwargs)

    def find_id(self, element_id, *args, **kwargs):
        return self.find_css(f'#{element_id}', *args, **kwargs)

    def find_name(self, element_name, *args, **kwargs):
        return self.find_css(f'[name={element_name}]', *args, **kwargs)

    def find_xpath(self, xpath, *args, **kwargs):
        return self.clean_elements(self.find_elements_by_xpath(xpath), xpath, *args, **kwargs)
