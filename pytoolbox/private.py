# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from bson.objectid import InvalidId, ObjectId
except:
    import uuid

    class ObjectId(uuid.UUID):
        def __init__(self, value):
            super(ObjectId, self).__init__(uuid.UUID('{{{0}}}'.format(value)))

        def binary(self):
            return self.hex

    class InvalidId(ValueError):
        pass


def _parse_kwargs_string(kwargs_string, **types):
    if not kwargs_string:
        return {}
    kwargs_list = [kwarg.strip().split('=') for kwarg in kwargs_string.split(';')]
    return {k: types[k](v) for k, v in kwargs_list}
