"""
Mix-ins for building your own test cases.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, overload

from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse

from pytoolbox import module
from pytoolbox.compat import override

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.http import HttpResponse, HttpResponseBase

    class _RestResponse(HttpResponse):
        """
        The response :class:`RestAPIMixin` returns: an `HttpResponse` also carrying `data`.

        A REST API test client parses the body and attaches it as `data`; the attribute is not on
        `HttpResponse` itself, and typing the methods as returning one hides it from every caller.
        Declared here rather than imported from `rest_framework` so that the type does not drag a
        dependency into the plain-Django half of this module.
        """

        data: Any


# Each mixin below completes a Django test case and reads its assertions and its client; naming the
# base under TYPE_CHECKING states that requirement for the checker only.
_TestMixin = TransactionTestCase if TYPE_CHECKING else object

_all = module.All(globals())


class _AssertNumQueriesInContext(CaptureQueriesContext):
    def __init__(
        self,
        test_case: TransactionTestCase,
        min_queries: int,
        max_queries: int,
        connection: BaseDatabaseWrapper,
    ) -> None:
        self.test_case = test_case
        self.min_queries = min_queries
        self.max_queries = max_queries
        super().__init__(connection)

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            executed = len(self)
            self.test_case.assertTrue(
                self.min_queries <= executed <= self.max_queries,
                f'{executed} queries executed, expected between '
                f'{self.min_queries} and {self.max_queries}{os.linesep}'
                f'Captured queries were:{os.linesep}'
                f'{os.linesep.join(query["sql"] for query in self.captured_queries)}',
            )


class ClearSiteCacheMixin(_TestMixin):
    """Clear the :class:`~django.contrib.sites.models.Site` cache before each test."""

    def clear_site_cache(self) -> None:
        """Clear the Django sites framework cache."""
        Site.objects.clear_cache()

    @override
    def setUp(self) -> None:
        """Clear the site cache before each test."""
        self.clear_site_cache()
        super().setUp()

    @override
    def assertNumQueries(self, *args: Any, **kwargs: Any) -> object:  # noqa: N802
        """Clear the site cache before asserting on the number of queries."""
        self.clear_site_cache()
        return super().assertNumQueries(*args, **kwargs)


class FixFlushMixin(_TestMixin):
    """Fix ``TransactionTestCase`` flush by enabling ``TRUNCATE CASCADE``."""

    def _fixture_teardown(self) -> None:
        """
        Fix TransactionTestCase tear-down by enabling TRUNCATE CASCADE. Issue with Django 1.8a1.
        """
        assert isinstance(self, TransactionTestCase)
        for db_name in self._databases_names(include_mirrors=False):  # pyrefly: ignore
            call_command(
                'flush',
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=self.available_apps is not None,
            )


class FormWizardMixin(_TestMixin):
    """Helpers for testing django-formtools wizard views."""

    def assertWizardSteps(self, response: Any, **kwargs: Any) -> None:  # noqa: N802
        """Assert that wizard step attributes match expected values."""
        for key, value in kwargs.items():
            self.assertEqual(getattr(response.context['wizard']['steps'], key), value, msg=key)

    def post_wizard(
        self,
        url: str,
        step: str,
        data: dict[str, Any] | None = None,
        raw_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> HttpResponseBase:
        """Post data to a specific wizard step."""
        from formtools.wizard.views import normalize_name

        name = normalize_name(resolve(reverse(url)).func.__name__)
        step_data = {f'{step}-{k}': v for k, v in data.items()} if data else {}
        step_data[f'{name}-current_step'] = step
        step_data.update(raw_data or {})
        return self.client.post(url, step_data, **kwargs)


class QueriesMixin(_TestMixin):
    """Provide assertions for checking the number of database queries."""

    @overload
    def assertNumQueriesIn(  # noqa: N802
        self,
        min_queries: int,
        max_queries: int,
        func: None = None,
        *args: Any,
        **kwargs: Any,
    ) -> _AssertNumQueriesInContext: ...

    @overload
    def assertNumQueriesIn(  # noqa: N802
        self,
        min_queries: int,
        max_queries: int,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None: ...

    def assertNumQueriesIn(  # noqa: N802
        self,
        min_queries: int,
        max_queries: int,
        func: Callable[..., Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> _AssertNumQueriesInContext | None:
        """
        Assert that the number of queries is between *min_queries* and
        *max_queries* (both inclusive).

        Called without *func* it returns the context manager, so that the overloads keep
        `with self.assertNumQueriesIn(1, 2):` typed as a context manager rather than as `object`.
        """
        connection = connections[kwargs.pop('using', DEFAULT_DB_ALIAS)]
        context = _AssertNumQueriesInContext(self, min_queries, max_queries, connection)
        if func is None:
            return context
        with context:
            func(*args, **kwargs)
        return None


class UrlMixin(_TestMixin):
    """Resolve URLs from view names, paths, or model instances."""

    def resolve(
        self,
        value: object,
        qs: str | None = None,
        urlconf: str | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        current_app: str | None = None,
    ) -> str:
        """Resolve *value* to a URL string, optionally appending a query string."""
        if isinstance(value, str) and '/' in value:
            url = value
        elif hasattr(value, 'get_absolute_url'):
            url = value.get_absolute_url()
        else:
            url = reverse(str(value), urlconf, args, kwargs, current_app)
        return url if qs is None else f'{url}?{qs}'


class RestAPIMixin(UrlMixin):
    """Convenience methods for testing REST API endpoints."""

    def _call(
        self,
        method: str,
        url: str,
        data: object,
        status: int,
        qs: str | None = None,
        urlconf: str | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        current_app: str | None = None,
        msg: Callable[[_RestResponse], object] = lambda r: getattr(r, 'data', r),
        **call_kwargs: Any,
    ) -> _RestResponse:
        url = self.resolve(url, qs, urlconf, args, kwargs, current_app)
        response = getattr(self.client, method)(url, data, **call_kwargs)
        self.assertEqual(response.status_code, status, msg(response))
        return response

    def delete(
        self,
        url: str,
        data: object = None,
        status: int = 204,
        **kwargs: Any,
    ) -> _RestResponse:
        """Send a DELETE request and assert the response status."""
        return self._call('delete', url, data, status, **kwargs)

    def get(
        self,
        url: str,
        data: object = None,
        status: int = 200,
        **kwargs: Any,
    ) -> _RestResponse:
        """Send a GET request and assert the response status."""
        return self._call('get', url, data, status, **kwargs)

    def patch(self, url: str, data: object, status: int = 200, **kwargs: Any) -> _RestResponse:
        """Send a PATCH request and assert the response status."""
        return self._call('patch', url, data, status, **kwargs)

    def post(self, url: str, data: object, status: int = 201, **kwargs: Any) -> _RestResponse:
        """Send a POST request and assert the response status."""
        return self._call('post', url, data, status, **kwargs)

    def put(self, url: str, data: object, status: int = 200, **kwargs: Any) -> _RestResponse:
        """Send a PUT request and assert the response status."""
        return self._call('put', url, data, status, **kwargs)


__all__ = _all.diff(globals())
