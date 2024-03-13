from __future__ import annotations

from django import dispatch as _dispatch

from pytoolbox.django.models import utils as _utils

__all__ = ['InstanceSignal', 'post_state_transition']


class InstanceSignal(_dispatch.Signal):

    def send(self, sender=None, **named):
        return super().send(_utils.get_base_model(sender or named['instance']), **named)

    def send_robust(self, sender=None, **named):
        return super().send(_utils.get_base_model(sender or named['instance']), **named)


post_state_transition = InstanceSignal()
