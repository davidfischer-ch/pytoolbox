# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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


def log_to_console(settings):
    """
    Update settings to make all loggers use the console.

    **Example usage**

    >>> from collections import namedtuple
    >>> settings = namedtuple('settings', ['DEBUG', 'LOGGING'])
    >>> settings.DEBUG = True
    >>> settings.LOGGING = {
    ...     'version': 1,
    ...     'loggers': {
    ...         'django': {
    ...             'handlers': ['file'], 'level': 'INFO', 'propagate': True
    ...         },
    ...         'django.request': {
    ...             'handlers': ['mail_admins'], 'level': 'ERROR', 'propagate': True
    ...         },
    ...         'mysite': {
    ...             'handlers': ['console'], 'level': 'INFO', 'propagate': True
    ...         }
    ...     }
    ... }
    >>> expected_settings = namedtuple('settings', ['DEBUG', 'LOGGING'])
    >>> expected_settings.DEBUG = True
    >>> expected_settings.LOGGING = {
    ...     'version': 1,
    ...     'loggers': {
    ...         'django': {
    ...             'handlers': ['console'], 'level': 'INFO', 'propagate': True
    ...         },
    ...         'django.request': {
    ...             'handlers': ['console'], 'level': 'ERROR', 'propagate': True
    ...         },
    ...         'mysite': {
    ...             'handlers': ['console'], 'level': 'INFO', 'propagate': True
    ...         }
    ...     }
    ... }
    >>> log_to_console(settings)
    >>> settings.LOGGING == expected_settings.LOGGING
    True
    """
    for logger in settings.LOGGING['loggers']:
        settings.LOGGING['loggers'][logger]['handlers'] = ['console']
