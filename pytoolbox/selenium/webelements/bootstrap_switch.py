from pytoolbox.selenium import Keys

__all__ = ['BootstrapSwitchMixin']


class BootstrapSwitchMixin(object):

    component = 'bootstrapSwitch'
    key_map = {True: Keys.RIGHT, False: Keys.LEFT}

    @staticmethod
    def clean_value(value):
        return {'on': True, 'off': False, True: True, False: False}[value]

    def send_keys(self, *value):
        return super().send_keys(*[self.key_map.get(v, v) for v in value])
