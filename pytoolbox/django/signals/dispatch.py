# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from django import dispatch as _dispatch

from pytoolbox import module as _module
from pytoolbox.django.models import utils as _utils

_all = _module.All(globals())


class InstanceSignal(_dispatch.Signal):

    def __init__(self, providing_args=None, use_caching=False):
        providing_args = providing_args or ['instance']
        if 'instance' not in providing_args:
            providing_args.insert(0, 'instance')
        super(InstanceSignal, self).__init__(providing_args, use_caching)

    def send(self, sender=None, **named):
        return super(InstanceSignal, self).send(
            _utils.get_base_model(sender or named['instance']), **named)

    def send_robust(self, sender=None, **named):
        return super(InstanceSignal, self).send(
            _utils.get_base_model(sender or named['instance']), **named)


post_state_transition = InstanceSignal(providing_args=['previous_state', 'args', 'kwargs'])

__all__ = _all.diff(globals())
