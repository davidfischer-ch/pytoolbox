# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from bson.objectid import InvalidId, ObjectId
except:
    InvalidId = ObjectId = None


def _parse_kwargs_string(kwargs_string, **types):
    if not kwargs_string:
        return {}
    kwargs_list = [kwarg.strip().split('=') for kwarg in kwargs_string.split(';')]
    return {k: types[k](v) for k, v in kwargs_list}
