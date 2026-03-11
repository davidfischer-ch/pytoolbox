"""
Mix-ins for building your own query-sets.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
import functools

from django.db import transaction

from pytoolbox import module

if TYPE_CHECKING:
    from django.db import models
    from django.db.models import QuerySet

_all = module.All(globals())


class AtomicGetUpdateOrCreateMixin:
    """Wrap ``get_or_create`` and ``update_or_create`` in atomic blocks."""

    savepoint = False

    def get_or_create(
            self,
            defaults: dict[str, object] | None = None,
            **kwargs: object
    ) -> tuple[models.Model, bool]:
        """Wrap ``get_or_create`` in an atomic transaction block."""
        with transaction.atomic(savepoint=self.savepoint):
            return super().get_or_create(defaults=defaults, **kwargs)

    def update_or_create(
            self,
            defaults: dict[str, object] | None = None,
            **kwargs: object
    ) -> tuple[models.Model, bool]:
        """Wrap ``update_or_create`` in an atomic transaction block."""
        with transaction.atomic(savepoint=self.savepoint):
            return super().update_or_create(defaults=defaults, **kwargs)


class AtomicGetRestoreOrCreateMixin:
    """Wrap ``get_restore_or_create`` in an atomic block."""

    savepoint = False

    def get_restore_or_create(self, *args: object, **kwargs: object) -> object:
        """Wrap ``get_restore_or_create`` in an atomic transaction block."""
        with transaction.atomic(savepoint=self.savepoint):
            return super().get_restore_or_create(*args, **kwargs)


class CreateModelMethodMixin:
    """Delegate ``create`` to the model's ``create`` class method if available."""

    def create(self, *args: object, **kwargs: object) -> models.Model:
        """Delegate to the model's ``create`` class method if available."""
        if hasattr(self.model, 'create'):
            return self.model.create(*args, **kwargs)
        return super().create(*args, **kwargs)
    create.alters_data = True


class StateMixin:
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

    def __getattr__(self, name: str) -> object:
        # avoid strange infinite recursion with defer()
        if name not in self._skip_names:
            all_states = set()
            for state_name in name.split('_or_'):
                states = self.model.states.get(state_name)
                if not states:
                    raise AttributeError
                method = all_states.add if isinstance(states, str) else all_states.update
                method(states)
            return functools.partial(self.in_states, all_states)
        raise AttributeError

    def in_states(self, states: set[str] | str, inverse: bool = False) -> QuerySet:
        """Filter query set to include instances in `states`."""
        method = self.exclude if inverse else self.filter
        return method(state__in={states} if isinstance(states, str) else states)


__all__ = _all.diff(globals())
