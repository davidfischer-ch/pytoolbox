# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module
from pytoolbox.selenium import Keys

_all = module.All(globals())


class BootstrapSwitchMixin(object):

    component = 'bootstrapSwitch'
    key_map = {True: Keys.RIGHT, False: Keys.LEFT}

    def clean_value(self, value):
        return {'on': True, 'off': False, True: True, False: False}[value]

    def send_keys(self, *value):
        return super(BootstrapSwitchMixin, self).send_keys(*[self.key_map.get(v, v) for v in value])


__all__ = _all.diff(globals())
