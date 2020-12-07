"""
Mix-ins for building your own test cases.
"""

import os

from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext

try:
    from django.urls import resolve, reverse
except ImportError:
    # For Django < 2.0
    from django.core.urlresolvers import resolve, reverse

from pytoolbox import module

_all = module.All(globals())


class _AssertNumQueriesInContext(CaptureQueriesContext):

    def __init__(self, test_case, num_range, connection):
        self.test_case = test_case
        self.range = num_range
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            executed = len(self)
            self.test_case.assertIn(
                executed,
                self.range,
                f'{executed} queries executed, {self.range} expected{os.linesep}'
                f'Captured queries were:{os.linesep}'
                f"{os.linesep.join(query['sql'] for query in self.captured_queries)}")


class ClearSiteCacheMixin(object):

    def clear_site_cache(self):
        Site.objects.clear_cache()

    def setUp(self):
        self.clear_site_cache()
        super().setUp()

    def assertNumQueries(self, *args, **kwargs):
        self.clear_site_cache()
        return super().assertNumQueries(*args, **kwargs)


class FixFlushMixin(object):

    def _fixture_teardown(self):
        """
        Fix TransactionTestCase tear-down by enabling TRUNCATE CASCADE. Issue with Django 1.8a1.
        """
        assert isinstance(self, TransactionTestCase)
        for db_name in self._databases_names(include_mirrors=False):
            call_command(
                'flush',
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,
                inhibit_post_migrate=self.available_apps is not None)


class FormWizardMixin(object):

    def assertWizardSteps(self, response, **kwargs):
        for key, value in kwargs.items():
            self.assertEqual(getattr(response.context['wizard']['steps'], key), value, msg=key)

    def post_wizard(self, url, step, data=None, raw_data=None, **kwargs):
        from formtools.wizard.views import normalize_name
        name = normalize_name(resolve(reverse(url)).func.__name__)
        step_data = {f'{step}-{k}': v for k, v in data.items()} if data else {}
        step_data[f'{name}-current_step'] = step
        step_data.update(raw_data or {})
        return self.post(url, step_data, **kwargs)


class QueriesMixin(object):

    def assertNumQueriesIn(self, num_range, func=None, *args, **kwargs):
        connection = connections[kwargs.pop('using', DEFAULT_DB_ALIAS)]
        context = _AssertNumQueriesInContext(self, num_range, connection)
        if func is None:
            return context
        with context:
            func(*args, **kwargs)


class UrlMixin(object):

    def resolve(self, value, qs=None, urlconf=None, args=None, kwargs=None, current_app=None):
        if isinstance(value, str) and '/' in value:
            url = value
        elif hasattr(value, 'get_absolute_url'):
            url = value.get_absolute_url()
        else:
            url = reverse(value, urlconf, args, kwargs, current_app)
        return url if qs is None else '{0}?{1}'.format(url, qs)


class RestAPIMixin(UrlMixin):

    def _call(
        self,
        method,
        url,
        data,
        status,
        qs=None,
        urlconf=None,
        args=None,
        kwargs=None,
        current_app=None,
        msg=lambda r: getattr(r, 'data', r),
        **call_kwargs
    ):
        url = self.resolve(url, qs, urlconf, args, kwargs, current_app)
        response = getattr(self.client, method)(url, data, **call_kwargs)
        self.assertEqual(response.status_code, status, msg(response))
        return response

    def delete(self, url, data=None, status=204, **kwargs):
        return self._call('delete', url, data, status, **kwargs)

    def get(self, url, data=None, status=200, **kwargs):
        return self._call('get', url, data, status, **kwargs)

    def patch(self, url, data, status=200, **kwargs):
        return self._call('patch', url, data, status, **kwargs)

    def post(self, url, data, status=201, **kwargs):
        return self._call('post', url, data, status, **kwargs)

    def put(self, url, data, status=200, **kwargs):
        return self._call('put', url, data, status, **kwargs)


__all__ = _all.diff(globals())
