from django import dispatch as _dispatch

from pytoolbox.django.models import utils as _utils

__all__ = ['InstanceSignal', 'post_state_transition']


class InstanceSignal(_dispatch.Signal):

    def __init__(self, providing_args=None, use_caching=False):
        providing_args = providing_args or ['instance']
        if 'instance' not in providing_args:
            providing_args.insert(0, 'instance')
        super().__init__(providing_args, use_caching)

    def send(self, sender=None, **named):
        return super().send(_utils.get_base_model(sender or named['instance']), **named)

    def send_robust(self, sender=None, **named):
        return super().send(_utils.get_base_model(sender or named['instance']), **named)


post_state_transition = InstanceSignal(providing_args=['previous_state', 'args', 'kwargs'])
