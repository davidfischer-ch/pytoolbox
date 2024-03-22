# pylint:disable=no-member
from __future__ import annotations


from . import client  # pylint:disable=unused-import

__all__ = ['LiveTestCaseMixin']


class LiveTestCaseMixin(object):

    live_client_class = client.LiveClient  # pylint:disable=used-before-assignment

    def setUp(self):  # pylint:disable=invalid-name
        """Call super's setUp and instantiate a live test client, only once."""
        super().setUp()
        if not hasattr(self.__class__, 'client'):
            self.__class__.client = self.live_client_class(self.live_server_url)
        self.client = self.__class__.client

    @classmethod
    def tearDownClass(cls):  # pylint:disable=invalid-name
        """Quit the live-test client and call super's tearDownClass."""
        if hasattr(cls, 'client'):
            cls.client.quit()
        super().tearDownClass()

    # Asserts

    def assertElementEqual(self, name, value, *, enabled=True):  # pylint:disable=invalid-name
        """Check the properties of an element. Works with both WebElement and Select."""
        if enabled:
            self.assertElementIsEnabled(name)
        else:
            self.assertElementIsDisabled(name)
        element = self.client.find_name(name)
        Select = self.client.web_driver.web_element_classes['select']  # pylint:disable=invalid-name
        if isinstance(element, Select):
            self.assertSelectOptions(name, value)
        else:
            self.assertElementValue(name, value)

    def assertElementIsDisabled(self, name, *args, **kwargs):  # pylint:disable=invalid-name
        self.assertFalse(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsEnabled(self, name, *args, **kwargs):  # pylint:disable=invalid-name
        self.assertTrue(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsReadOnly(self, name):  # pylint:disable=invalid-name
        self.assertIsNotNone(self.client.find_name(name).get_attribute('readonly'))

    def assertElementValue(self, name, value, *args, **kwargs):  # pylint:disable=invalid-name
        element = self.client.find_name(name)
        operator = kwargs.pop('operator', lambda x: x)
        self.assertEqual(
            operator(element.get_attribute('value')),
            element.clean_value(value),
            *args,
            **kwargs)

    def assertSelectOptions(self, name, texts, *args, **kwargs):  # pylint:disable=invalid-name
        self.assertListEqual(
            sorted(o.text for o in self.client.find_name(name).all_selected_options),
            sorted([texts] if isinstance(texts, str) else texts), *args, **kwargs)
