"""
Mixin for Selenium-based live test cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pytoolbox.compat import override

from . import client  # pylint:disable=unused-import

if TYPE_CHECKING:
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase

# The mixin completes a live-server test case: it calls its assertions and reads the URL that
# case serves on. Naming the base under TYPE_CHECKING states that requirement for the checker
# while leaving the mixin plain at runtime, where it must stay to the left of the test case.
_LiveTestCaseMixin = StaticLiveServerTestCase if TYPE_CHECKING else object

__all__ = ['LiveTestCaseMixin']


class LiveTestCaseMixin(_LiveTestCaseMixin):
    """Mixin that provides a shared :class:`LiveClient` for live server tests."""

    live_client_class = client.LiveClient  # pylint:disable=used-before-assignment

    # Built once per test case class by setUp, and shared by every test in it.
    client: ClassVar[client.LiveClient]  # type: ignore[assignment]

    @override
    def setUp(self) -> None:  # pylint:disable=invalid-name
        """Call super's setUp and instantiate a live test client, only once."""
        super().setUp()
        if not hasattr(type(self), 'client'):
            type(self).client = self.live_client_class(self.live_server_url)

    @classmethod
    @override
    def tearDownClass(cls) -> None:  # pylint:disable=invalid-name
        """Quit the live-test client and call super's tearDownClass."""
        if hasattr(cls, 'client'):
            cls.client.quit()
        super().tearDownClass()

    # Asserts

    def assertElementEqual(  # noqa: N802
        self,
        name: str,
        value: str,
        *,
        enabled: bool = True,
    ) -> None:
        """Check the properties of an element. Works with both WebElement and Select."""
        if enabled:
            self.assertElementIsEnabled(name)
        else:
            self.assertElementIsDisabled(name)
        element = self.client.find_name(name)
        Select = self.client.web_driver.web_element_classes['select']  # noqa: N806
        if isinstance(element, Select):
            self.assertSelectOptions(name, value)
        else:
            self.assertElementValue(name, value)

    def assertElementIsDisabled(  # noqa: N802
        self,
        name: str,
        *args,
        **kwargs,
    ) -> None:
        """Assert the named element is disabled."""
        self.assertFalse(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsEnabled(  # noqa: N802
        self,
        name: str,
        *args,
        **kwargs,
    ) -> None:
        """Assert the named element is enabled."""
        self.assertTrue(self.client.find_name(name).is_enabled(), *args, **kwargs)

    def assertElementIsReadOnly(self, name: str) -> None:  # noqa: N802
        """Assert the named element has a ``readonly`` attribute."""
        self.assertIsNotNone(self.client.find_name(name).get_attribute('readonly'))

    def assertElementValue(  # noqa: N802
        self,
        name: str,
        value: str,
        *args,
        **kwargs,
    ) -> None:
        """Assert the named element's value equals the expected value."""
        element = self.client.find_name(name)
        operator = kwargs.pop('operator', lambda x: x)
        self.assertEqual(
            operator(element.get_attribute('value')),
            element.clean_value(value),
            *args,
            **kwargs,
        )

    def assertSelectOptions(  # noqa: N802
        self,
        name: str,
        texts: str | list[str],
        *args,
        **kwargs,
    ) -> None:
        """Assert the selected options of a ``<select>`` match the given texts."""
        self.assertListEqual(
            sorted(o.text for o in self.client.find_name(name).all_selected_options),
            sorted([texts] if isinstance(texts, str) else texts),
            *args,
            **kwargs,
        )
