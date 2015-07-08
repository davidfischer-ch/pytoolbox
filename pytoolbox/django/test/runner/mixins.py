# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
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

import tempfile
from django.conf import settings

from .... import module

_all = module.All(globals())


class CeleryInMemoryMixin(object):

    def setup_test_environment(self):
        super(CeleryInMemoryMixin, self).setup_test_environment()
        settings.BROKER_BACKEND = 'memory'
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        settings.CELERY_ALWAYS_EAGER = True


class FastPasswordHasherMixin(object):

    def setup_test_environment(self):
        super(FastPasswordHasherMixin, self).setup_test_environment()
        settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher', )


class TemporarySendfileRootMixin(object):

    def setup_test_environment(self):
        super(TemporarySendfileRootMixin, self).setup_test_environment()
        settings.SENDFILE_ROOT = tempfile.mkdtemp()

__all__ = _all.diff(globals())
