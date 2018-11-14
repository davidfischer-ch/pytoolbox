# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own query-sets.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import functools

from django.db import transaction

from pytoolbox import module
from pytoolbox.encoding import string_types

_all = module.All(globals())


class AtomicGetUpdateOrCreateMixin(object):

    savepoint = False

    def get_or_create(self, defaults=None, **kwargs):
        with transaction.atomic(savepoint=self.savepoint):
            return super(AtomicGetUpdateOrCreateMixin, self).get_or_create(
                defaults=defaults, **kwargs)

    def update_or_create(self, defaults=None, **kwargs):
        with transaction.atomic(savepoint=self.savepoint):
            return super(AtomicGetUpdateOrCreateMixin, self).update_or_create(
                defaults=defaults, **kwargs)


class AtomicGetRestoreOrCreateMixin(object):

    savepoint = False

    def get_restore_or_create(self, *args, **kwargs):
        with transaction.atomic(savepoint=self.savepoint):
            return super(AtomicGetRestoreOrCreateMixin, self).get_restore_or_create(*args, **kwargs)


class CreateModelMethodMixin(object):

    def create(self, *args, **kwargs):
        if hasattr(self.model, 'create'):
            return self.model.create(*args, **kwargs)
        return super(CreateModelMethodMixin, self).create(*args, **kwargs)
    create.alters_data = True


class StateMixin(object):
    """
    Generate on the fly utility query-set filtering methods to a model using a
    :class:`pytoolbox.states.StateEnum` to implement its own state machine. Then you can use
    something like ``Model.objects.ready_or_canceled(inverse=True)`` to exclude models in state
    READY or CANCELED.

    This mixin requires the following to work:

    * Add a `states` attribute to your model class set to the states class you defined earlier.
    * Add a `state` field to the model for saving instance state in database.
    """

    _skip_names = frozenset(['__getstate__', 'model'])

    def __getattr__(self, name):
        # avoid strange infinite recursion with defer()
        if name not in self._skip_names:
            all_states = set()
            for name in name.split('_or_'):
                states = self.model.states.get(name)
                if not states:
                    raise AttributeError
                method = all_states.add if isinstance(states, string_types) else all_states.update
                method(states)
            return functools.partial(self.in_states, all_states)
        raise AttributeError

    def in_states(self, states, inverse=False):
        """Filter query set to include instances in `states`."""
        method = self.exclude if inverse else self.filter
        return method(state__in={states} if isinstance(states, string_types) else states)


__all__ = _all.diff(globals())
