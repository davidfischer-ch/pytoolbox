# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.urlresolvers import reverse
from django.db import connections, DEFAULT_DB_ALIAS
from django.test.utils import CaptureQueriesContext

__all__ = ('QueriesMixin', 'RestAPIMixin')


class _AssertNumQueriesInContext(CaptureQueriesContext):

    def __init__(self, test_case, num_range, connection):
        self.test_case = test_case
        self.range = num_range
        super(_AssertNumQueriesInContext, self).__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super(_AssertNumQueriesInContext, self).__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            executed = len(self)
            self.test_case.assertIn(
                executed, self.range, '{0} queries executed, {1.range} expected\nCaptured queries were:\n{2}'.format(
                    executed, self, '\n'.join(query['sql'] for query in self.captured_queries)
                )
            )


class QueriesMixin(object):

    def assertNumQueriesIn(self, num_range, func=None, *args, **kwargs):
        connection = connections[kwargs.pop('using', DEFAULT_DB_ALIAS)]
        context = _AssertNumQueriesInContext(self, num_range, connection)
        if func is None:
            return context
        with context:
            func(*args, **kwargs)


class RestAPIMixin(object):

    def _call_api(self, method, url, data, status, qs=None, **kwargs):
        method, url = getattr(self.client, method), reverse(url) if 'http' not in url else url
        response = method(url + ('?%s' % qs if qs is not None else ''), data, **kwargs)
        self.assertEqual(response.status_code, status, response.data)
        return response

    def delete(self, url, data=None, status=204, **kwargs):
        return self._call_api('delete', url, data, status, **kwargs)

    def get(self, url, data=None, status=200, **kwargs):
        return self._call_api('get', url, data, status, **kwargs)

    def patch(self, url, data, status=200, **kwargs):
        return self._call_api('patch', url, data, status, **kwargs)

    def post(self, url, data, status=201, **kwargs):
        return self._call_api('post', url, data, status, **kwargs)

    def put(self, url, data, status=200, **kwargs):
        return self._call_api('put', url, data, status, **kwargs)
