# pylint:disable=no-member
"""
Mixin for Selenium-based live test cases.
"""
from __future__ import annotations


from . import client  # pylint:disable=unused-import

__all__ = ['LiveTestCaseMixin']


class LiveTestCaseMixin(object):
    """Mixin that provides a shared :class:`LiveClient` for live server tests."""

    live_client_class = client.LiveClient  # pylint:disable=used-before-assignment

    def setUp(self) -> None:  # pylint:disable=invalid-name
        """Call super's setUp and instantiate a live test client, only once."""
        super().setUp()
        if not hasattr(type(self), 'client'):
            type(self).client = self.live_client_class(self.live_server_url)
        self.client = type(self).client

    @classmethod
    def tearDownClass(cls) -> None:  # pylint:disable=invalid-name
        """Quit the live-test client and call super's tearDownClass."""
        if hasattr(cls, 'client'):
            cls.client.quit()
        super().tearDownClass()

    # Asserts

    def assertElementEqual(  # pylint:disable=invalid-name
            self,
            name: str,
            value: str,
            *,
            enabled: bool = True) -> None:
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

    def assertElementIsDisabled(  # pylint:disable=invalid-name
            self,
            name: str,
            *args,
            **kwargs) -> None:
        """Assert the named element is disabled."""
        self.assertFalse(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsEnabled(  # pylint:disable=invalid-name
            self,
            name: str,
            *args,
            **kwargs) -> None:
        """Assert the named element is enabled."""
        self.assertTrue(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsReadOnly(self, name: str) -> None:  # pylint:disable=invalid-name
        """Assert the named element has a ``readonly`` attribute."""
        self.assertIsNotNone(self.client.find_name(name).get_attribute('readonly'))

    def assertElementValue(  # pylint:disable=invalid-name
            self,
            name: str,
            value: str,
            *args,
            **kwargs) -> None:
        """Assert the named element's value equals the expected value."""
        element = self.client.find_name(name)
        operator = kwargs.pop('operator', lambda x: x)
        self.assertEqual(
            operator(element.get_attribute('value')),
            element.clean_value(value),
            *args,
            **kwargs)

    def assertSelectOptions(  # pylint:disable=invalid-name
            self,
            name: str,
            texts: str | list[str],
            *args,
            **kwargs) -> None:
        """Assert the selected options of a ``<select>`` match the given texts."""
        self.assertListEqual(
            sorted(o.text for o in self.client.find_name(name).all_selected_options),
            sorted([texts] if isinstance(texts, str) else texts), *args, **kwargs)
