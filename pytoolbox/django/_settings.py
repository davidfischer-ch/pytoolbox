# -*- encoding: utf-8 -*-

"""
Django settings file for documenting the project.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
SECRET_KEY = 'AWESOME-SECRET-KEY'
