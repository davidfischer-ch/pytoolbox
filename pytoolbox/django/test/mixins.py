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

from django.db import connections, DEFAULT_DB_ALIAS
from django.test.utils import CaptureQueriesContext

__all__ = ('QueriesMixin', )


class _AssertNumQueriesContext(CaptureQueriesContext):

    def __init__(self, callback, num, connection):
        self.callback = callback
        self.num = num
        super(_AssertNumQueriesContext, self).__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super(_AssertNumQueriesContext, self).__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            executed = len(self)
            self.callback(executed, self.num, "%d queries executed, %d expected\nCaptured queries were:\n%s" % (
                executed, self.num, '\n'.join(query['sql'] for query in self.captured_queries))
            )


class QueriesMixin(object):

    def assertNumQueries(self, num, callback=None, func=None, *args, **kwargs):
        using = kwargs.pop("using", DEFAULT_DB_ALIAS)
        conn = connections[using]
        context = _AssertNumQueriesContext(callback or self.assertEqual, num, conn)
        if func is None:
            return context
        with context:
            func(*args, **kwargs)
