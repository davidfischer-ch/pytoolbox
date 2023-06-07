# pylint:disable=no-member

from pytoolbox.selenium import common, Keys

__all__ = ['BootstrapSwitchMixin']


class BootstrapSwitchMixin(common.FindMixin):

    component = 'bootstrapSwitch'
    key_map = {True: Keys.RIGHT, False: Keys.LEFT}

    @staticmethod
    def clean_value(value):
        return {'on': True, 'off': False, True: True, False: False}[value]

    def send_keys(self, *value):
        return super().send_keys(*[self.key_map.get(v, v) for v in value])
