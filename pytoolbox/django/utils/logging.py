# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

_all = module.All(globals())


def log_to_console(settings):
    """
    Update settings to make all loggers use the console.

    **Example usage**

    >>> import collections
    >>> settings = collections.namedtuple('settings', ['DEBUG', 'LOGGING'])
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
    >>> expected_settings = collections.namedtuple('settings', ['DEBUG', 'LOGGING'])
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


__all__ = _all.diff(globals())
