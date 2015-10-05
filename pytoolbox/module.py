# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

__all__ = ('All', )


class All(object):

    def __init__(self, globals_):
        self.init_keys = set(globals_.iterkeys())

    def diff(self, globals_, to_type=list):
        new_keys = set(globals_.iterkeys()) - self.init_keys
        return to_type(k for k in new_keys if k[0] != '_')
