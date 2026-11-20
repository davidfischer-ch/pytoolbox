"""
Mixins for building your own models.

Put :class:`BatteriesIncludedModelMixin` left of :class:`~django.db.models.Model` and of the
abstract models in a model's bases, and :class:`BetterUniquenessErrorsMixin` between it and
:class:`~django.db.models.Model`.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import collections
import contextlib
import itertools
import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Final, Self, override

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import models, router, transaction
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query_utils import DeferredAttribute
from django.db.utils import IntegrityError

from pytoolbox import comparison, module
from pytoolbox import exceptions as py_exceptions
from pytoolbox import itertools as py_itertools
from pytoolbox.django import signals
from pytoolbox.django.core import exceptions
from pytoolbox.types import Missing

from . import utils

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator, Sequence
    from types import CodeType

    from django.db.models import QuerySet
    from django.db.models import options as meta_module
    from django.db.models.base import ModelBase

    from pytoolbox.states import StateEnum

# Every mixin below completes a Model and reads its attributes (`pk`, `_meta`, `save`, ...). Naming
# Model as the base under TYPE_CHECKING states that requirement for the checker while leaving the
# mixins plain at runtime, where they must stay to the left of the model class.
_ModelMixin = models.Model if TYPE_CHECKING else object

_all = module.All(globals())


class BatteriesIncludedModelMixin(_ModelMixin):
    """
    An opinionated model mixin, batteries included, each battery set up by a class attribute.

    Its :meth:`save` runs, in this order:

    **Forced insert** (always on)

    Automatically set ``force_insert`` based on the instance's adding state. Models with a primary
    key preset to a value before being saved in database are correctly handled: Django otherwise
    tries an UPDATE first for a primary key set before the first save, which writes over the row
    holding that key.

    Configuration:

    * Another choice for one save: pass ``force_insert`` to :meth:`save`.

    **State transition hook** (off by default, on a state machine)

    Set the fields a transition implies, such as a completion date, in the save making it. Before
    its validation, a save writing a ``state`` other than the previous one calls
    :meth:`on_state_transition` with that previous state: ``previous_state``, or ``None`` for an
    insert. The fields it assigns are validated, tracked and written by that same save, a save
    limited by ``update_fields`` included. A save not writing ``state`` does not call it.

    Configuration:

    * Fields a transition sets, such as a completion date, in the same save: override
      :meth:`on_state_transition`.

    **Validation on save** (on by default)

    Run :meth:`~django.db.models.Model.full_clean` automatically before every save, before any
    field's ``pre_save``: invalid data is stopped before anything is written, an upload included.
    Deferred fields are left out, and so are the fields a save limited by ``update_fields`` does
    not write, unless a uniqueness or a constraint check names one with a field the save writes:
    such a field is validated as it stands, read from the database when deferred, and the check
    runs. The model's :meth:`~django.db.models.Model.clean` runs all the same. The values the
    fields' ``pre_save`` assigns are not validated.

    Configuration:

    * No validation: set ``validate_on_save = False``, or call ``save(validate=False)``.
    * Do not validate uniqueness nor relation fields on save to prevent excessive SELECT queries:
      pass the keyword arguments of ``full_clean`` in ``validate_on_save_kwargs``, such as
      ``{'validate_unique': False}``.
    * Validation that depends on the model or the save, such as every relation field left out:
      override :meth:`get_validation_kwargs`.

    **Fields pre_save** (always on)

    If you wanna be sure the fields pre_save method are called, now you can! The ``pre_save`` of
    each field a save may write runs, not the primary key, a generated or a deferred field: Django's
    own save calls it only for the fields it writes. The values it assigns, such as an ``auto_now``
    date, are tracked and written by the same save.

    For more information see: https://code.djangoproject.com/ticket/25363

    Configuration: none, it always runs.

    **Update fields tracking** (on by default)

    Keep track of what fields were set in order to make UPDATE queries lighter, and to write no
    field back over another process's change: ``update_fields`` is derived from the fields
    assigned since the instance was read or saved. Foreign keys are correctly handled: assigning a
    related object tracks its foreign key. A field reloaded from the database, by
    :meth:`~django.db.models.Model.refresh_from_db` or a deferred field loaded, is no assignment.

    This low-memory footprint tracking also comes with some limitations, it does not:

    * Store old fields values: you cannot know if the fields are really modified or not.
    * Watch for background modifications of the mutable fields, it can drive you crazy, sometimes:
      a list or a dict of a ``JSONField`` changed in place is no assignment.

    Configuration:

    * Every field written by every save, nothing tracked: set ``track_update_fields = False``.
    * The fields of one save: pass ``update_fields`` to :meth:`save`. A value changed in place is
      written this way, or by assigning it again.

    **Fields always updated** (off by default)

    Ensure fields listed in the attribute ``always_update_fields`` are always updated by
    ``self.save()``, a save limited by ``update_fields`` included. Makes the usage of
    ``self.save(update_fields=...)`` cleaner.

    Configuration:

    * A field written by every save, such as a timestamp: list it in ``always_update_fields``.
    * Fields written together, such as a total whenever a price is written: override
      :meth:`get_update_fields`.

    **Forced update** (on by default)

    The update of a row read from the database is forced, for a save given no ``force_update``: a
    row deleted meanwhile raises instead of being inserted again.

    Configuration:

    * The update left unforced: set ``default_force_update = False``, or pass ``force_update`` to
      :meth:`save`.

    **Primary key and copies** (always on)

    If the primary key is set but unchanged, then remove the primary key from the list of fields to
    update. This fixes an issue when saving, ``ValueError: The following fields do not exist in this
    model, are m2m fields, primary keys, or are non-concrete fields: id``. This check is probably
    implemented by Django developers to protect from unintentional data overwrite.

    If the primary key is set to a new value, then the intention of the developer is probably to
    duplicate the model by saving it with a new primary key. So the save lets Django insert a copy
    of the row, every field written.

    Configuration: none.

    **Update preconditions** (off by default)

    Guard row updates with filter/exclude preconditions for optimistic concurrency. The update of
    each table writes the row only when it matches all of the filters and none of the exclusions.
    An update failing them writes nothing and raises ``precondition_error_class``.

    Configuration:

    * The preconditions of one save: call ``save(pre_filters=..., pre_excludes=...)``.
    * Preconditions on every save: override :meth:`get_preconditions`.
    * Another exception: set ``precondition_error_class``.

    **State machine** (off by default, on once ``states`` is declared)

    Add state-based preconditions to row updates for safe transitions. A model declaring ``states``
    is a state machine: an update writing its ``state`` field fails unless ``states`` declares a
    transition from the stored state to the one written. A state ``states`` does not declare, or
    NULL, moves into no state.

    Configuration:

    * A state machine on the ``state`` field: set ``states`` to its
      :class:`~pytoolbox.states.StateEnum`.
    * An update writing ``state`` without the transition guard: set ``check_state = False``, call
      ``save(check_state=False)``, or name ``state`` in the save's own preconditions.
    * Other exceptions: set ``transition_not_allowed_error_class`` and
      ``invalid_state_error_class``.

    **State transition events** (on with a state machine)

    Send :data:`~pytoolbox.django.signals.post_state_transition` after state changes: when a save
    wrote a ``state`` other than ``previous_state``, which is then updated first, and once only
    when a receiver saves the instance again.

    Configuration:

    * React to a transition: connect a receiver to
      :data:`~pytoolbox.django.signals.post_state_transition`.

    **Asynchronous save** (always on)

    :meth:`asave` forces the insert and the update as :meth:`save` does.

    Configuration:

    * The same keywords as :meth:`save`.
    """

    #: The fields written by each save limited by ``update_fields``, such as a timestamp. It makes
    #: the usage of ``save(update_fields=...)`` cleaner.
    always_update_fields: ClassVar[tuple[str, ...]] = ()

    #: Whether an update writing ``state`` is guarded by the transitions declared in ``states``.
    check_state: ClassVar[bool] = True

    #: Whether the update of a row read from the database is forced, for a save given no
    #: ``force_update``.
    default_force_update: ClassVar[bool] = True

    #: The exception :meth:`check_state_in` raises for a state out of those given.
    invalid_state_error_class: ClassVar[type[py_exceptions.MessageMixin]] = (
        exceptions.InvalidStateError
    )

    #: The exception raised by an update whose row fails its preconditions.
    precondition_error_class: ClassVar[type[py_exceptions.MessageMixin]] = (
        exceptions.DatabaseUpdatePreconditionsError
    )

    #: The :class:`~pytoolbox.states.StateEnum` of the ``state`` field, ``None`` for a model without
    #: one.
    states: ClassVar[type[StateEnum] | None] = None

    #: Whether ``update_fields`` is derived from the fields assigned, for a save not given them.
    track_update_fields: ClassVar[bool] = True

    #: The exception :meth:`can_transit_to` raises for a transition not declared in ``states``.
    transition_not_allowed_error_class: ClassVar[type[py_exceptions.MessageMixin]] = (
        exceptions.TransitionNotAllowedError
    )

    #: Whether each save calls :meth:`~django.db.models.Model.full_clean` first.
    validate_on_save: ClassVar[bool] = True

    #: Keyword arguments forwarded to :meth:`~django.db.models.Model.full_clean`.
    validate_on_save_kwargs: ClassVar[dict[str, Any]] = {}

    #: The primary key last read from or written to the database.
    previous_pk: Any

    #: The state last read from or written to the database, on a model declaring ``states``.
    #:
    #: It is :data:`~pytoolbox.types.Missing` while a deferred state is unread.
    previous_state: Any

    # Supplied by a model declaring states: its current state.
    state: Any

    # The attnames of the fields a save may write, set on each model class by _get_field_attnames.
    _field_attnames: ClassVar[frozenset[str]]

    # The check_state of the save running, which _do_update reads.
    _check_state: bool = True

    # The preconditions of the save running, which _do_update applies.
    _preconditions: Preconditions | None = None

    # Set while refresh_from_db assigns the values it reads.
    _reloading: bool = False

    # --- Save pipeline ----------------------------------------------------------------------------

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._assigned_fields: set[str] = set()
        self.previous_pk = self.pk
        if self.states is not None:
            # Read from the instance: reading a deferred state would query the database.
            self.previous_state = self.__dict__.get('state', Missing)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """Track an assignment to a field of a row read from the database, its loading aside."""
        if name in self._get_field_attnames() and not self._state.adding:
            # A deferred field loaded with its peers is assigned by DeferredAttribute.fetch_many.
            if self._reloading or (
                name not in self.__dict__ and sys._getframe(1).f_code is _FETCH_MANY_CODE
            ):
                self._assigned_fields.discard(name)
                if name == 'state' and self.states is not None:
                    self.previous_state = value
            elif self.track_update_fields:
                self._assigned_fields.add(name)
        super().__setattr__(name, value)

    @override
    def __setstate__(self, state: dict[str, Any]) -> None:  # pyrefly: ignore[bad-override]
        """Restore a pickled or copied instance, its assignments tracked apart from the original."""
        # django-stubs does not declare Model.__setstate__: neither @override nor the super() call
        # below is checked against it.
        # pyrefly: ignore[missing-attribute]
        super().__setstate__(state)
        self._assigned_fields = set(self._assigned_fields)

    # TODO: Django's asave() runs save() in a thread (sync_to_async), as this one does. Make this
    # one native once Django's is:
    # tests/test_django_models_mixins.py::test_django_asave_still_runs_save fails then.
    @override
    async def asave(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] | None = None,
        force_update: bool | None = None,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        check_state: bool | None = None,
        pre_excludes: dict[str, Any] | None = None,
        pre_filters: dict[str, Any] | None = None,
        validate: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Save the instance as :meth:`save` does, from asynchronous code."""
        await sync_to_async(self.save)(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            check_state=check_state,
            pre_excludes=pre_excludes,
            pre_filters=pre_filters,
            validate=validate,
            **kwargs,
        )

    @override
    def clean_fields(self, exclude: Collection[str] | None = None) -> None:
        """Clean the fields, a field cleaned counted as assigned only when its value changed."""
        with self._assigning_changes_only():
            super().clean_fields(exclude=exclude)

    @override
    def full_clean(
        self,
        exclude: Iterable[str] | None = None,
        validate_unique: bool = True,
        validate_constraints: bool = True,
    ) -> None:
        """
        Validate the instance, a field counted as assigned only when the validation changed its
        value, as the model's :meth:`~django.db.models.Model.clean` may.
        """
        with self._assigning_changes_only():
            super().full_clean(
                exclude=exclude,
                validate_unique=validate_unique,
                validate_constraints=validate_constraints,
            )

    def get_preconditions(
        self,
        fields: frozenset[str],
        *,
        check_state: bool,
        pre_excludes: dict[str, Any],
        pre_filters: dict[str, Any],
    ) -> Preconditions:
        """
        Return the preconditions of an update of *fields*.

        These are the save's ``pre_excludes`` and ``pre_filters``, with a filter on the states
        having a transition into the ``state`` written added when ``check_state`` holds and the
        save's own preconditions leave ``state`` free. Override it to guard the updates with lookups
        of the model's own.
        """
        if (
            self.states is None
            or not check_state
            or 'state' not in fields
            or any(
                lookup.split(LOOKUP_SEP, 1)[0] == 'state'
                for lookup in itertools.chain(pre_excludes, pre_filters)
            )
        ):
            return Preconditions(pre_excludes=pre_excludes, pre_filters=pre_filters)

        # A stored state ``states`` does not declare matches no filter, and moves into no state.
        states = self.states.get_transit_from(self.state)
        key, value = ('state', next(iter(states))) if len(states) == 1 else ('state__in', states)
        return Preconditions(pre_excludes=pre_excludes, pre_filters={**pre_filters, key: value})

    def get_update_fields(self, update_fields: frozenset[str] | None) -> frozenset[str] | None:
        """
        Return the fields this save writes, ``None`` for every field.

        *update_fields* are those derived: the save's own, else the fields assigned, with
        ``always_update_fields``. A save calls it before its validation and again after the fields'
        ``pre_save``. Override it to write fields together.
        """
        return update_fields

    def get_validation_kwargs(self, update_fields: frozenset[str] | None) -> dict[str, Any]:
        """
        Return the keyword arguments of the :meth:`full_clean` of a save writing *update_fields*.

        These are ``validate_on_save_kwargs``, with the deferred fields and the fields the save does
        not write added to ``exclude``, but those a uniqueness or a constraint check names with a
        field the save writes. *update_fields* is ``None`` for a save of every field.
        """
        kwargs = dict(self.validate_on_save_kwargs)
        deferred = self.get_deferred_fields()
        unwritten = {
            f.name
            for f in self._meta.concrete_fields
            if f.attname in deferred
            or (
                update_fields is not None
                and f.name not in update_fields
                and f.attname not in update_fields
            )
        }
        written = {f.name for f in self._meta.concrete_fields} - unwritten
        checked = {
            name for names in self._get_checked_field_groups() if names & written for name in names
        }
        if excluded := [
            f.name
            for f in self._meta.concrete_fields
            if f.name in unwritten and f.name not in checked
        ]:
            kwargs['exclude'] = [*kwargs.get('exclude', ()), *excluded]
        return kwargs

    def on_state_transition(self, previous_state: Any) -> None:
        """
        Set the fields a transition implies, before the validation of a save writing a new state.

        *previous_state* is ``previous_state``, or ``None`` for an insert. The fields it assigns are
        validated, tracked and written by that save, a save limited by ``update_fields`` included.
        It does nothing by default.
        """

    @override
    def refresh_from_db(
        self,
        using: str | None = None,
        fields: Iterable[str] | None = None,
        from_queryset: QuerySet | None = None,
    ) -> None:
        """
        Reload the fields from the database.

        A field reloaded is no assignment for a save to write, and a state reloaded becomes
        ``previous_state``.
        """
        self._reloading = True
        try:
            super().refresh_from_db(using=using, fields=fields, from_queryset=from_queryset)
        finally:
            self._reloading = False

    @override
    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] | None = None,
        force_update: bool | None = None,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        check_state: bool | None = None,
        pre_excludes: dict[str, Any] | None = None,
        pre_filters: dict[str, Any] | None = None,
        validate: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Save the instance through the steps the class lists.

        ``check_state`` and ``validate`` override the class options for this save. Its update writes
        a row matching none of ``pre_excludes`` and all of ``pre_filters``, or raises
        ``precondition_error_class``.
        """
        if force_insert is None:
            force_insert = self._state.adding
        updating = not self._state.adding and not force_insert
        if force_update is None:
            force_update = updating and self.default_force_update
        if update_fields is not None:
            update_fields = frozenset(update_fields)

        # Before the validation, which covers the fields the hook assigns.
        if self._writes_state(self._get_update_fields(update_fields, updating=updating)):
            previous_state = None if self._state.adding else self.previous_state
            if self.state != previous_state:
                values = dict(self.__dict__)
                self.on_state_transition(previous_state)
                if update_fields is not None:
                    # A save limited by update_fields writes the fields the hook changed as well.
                    update_fields |= {
                        name
                        for name in self._get_field_attnames()
                        if name in self.__dict__
                        and not comparison.is_equal(self.__dict__[name], values.get(name, Missing))
                    }

        if self.validate_on_save if validate is None else validate:
            self.full_clean(
                **self.get_validation_kwargs(
                    self._get_update_fields(update_fields, updating=updating)
                )
            )

        # After the validation, to keep a row that fails it from storing its upload.
        deferred = self.get_deferred_fields()
        for field in self._meta.local_concrete_fields:
            if not field.primary_key and not field.generated and field.attname not in deferred:
                field.pre_save(self, self._state.adding)

        update_fields = self._get_update_fields(update_fields, updating=updating)
        if updating and update_fields is None and self.pk != self.previous_pk:
            # A copy of the row, which Django inserts where no row holds its primary key.
            force_update = False

        # Restored after: a save nested in this one, as a pre_save receiver's, keeps the outer
        # save's guard.
        outer_check_state, outer_preconditions = self._check_state, self._preconditions
        self._check_state = self.check_state if check_state is None else check_state
        self._preconditions = Preconditions(
            pre_excludes=pre_excludes or {},
            pre_filters=pre_filters or {},
        )
        try:
            super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
                **kwargs,
            )
        finally:
            self._check_state, self._preconditions = outer_check_state, outer_preconditions

        self.previous_pk = self.pk
        if update_fields is None:
            self._assigned_fields.clear()
        else:
            self._assigned_fields -= {
                f.attname
                for f in self._meta.concrete_fields
                if f.name in update_fields or f.attname in update_fields
            }

        if self._writes_state(update_fields):
            # Updated before the signal: a receiver saving the instance again reads the new state.
            previous_state, self.previous_state = self.previous_state, self.state
            if self.state != previous_state:
                signals.post_state_transition.send(
                    args=(),
                    instance=self,
                    kwargs={'update_fields': update_fields},
                    previous_state=previous_state,
                )

    # --- State machine ----------------------------------------------------------------------------

    def can_transit_to(self, state: str, *, fail: bool = False, noop_skip: bool = False) -> bool:
        """
        Return whether ``states`` declares a transition from the current state to *state*.

        * ``True`` if it does.
        * ``False`` if it does not and ``fail`` is off, or ``noop_skip`` is on and *state* is the
          current one.
        * Else raise ``transition_not_allowed_error_class``.
        """
        if self.states is None:
            raise TypeError(f'{type(self).__name__} declares no states.')
        if state in self.states.TRANSITIONS[self.state]:
            return True
        if not fail or noop_skip and self.state == state:
            return False
        raise self.transition_not_allowed_error_class(instance=self, state=state)

    def check_state_in(self, states: Iterable[str] | str, *, fail: bool = False) -> bool:
        """
        Return ``True`` if the current state is in *states*.

        Else return ``False``, or raise ``invalid_state_error_class`` with ``fail`` on.
        """
        states = sorted(py_itertools.chain(states))
        if self.state in states:
            return True
        if not fail:
            return False
        raise self.invalid_state_error_class(instance=self, states=states)

    # --- Accessors --------------------------------------------------------------------------------

    @classmethod
    def get_related_manager(cls, field: str) -> models.Manager:
        """
        Provide shortcuts to access related model classes and managers: the default manager of the
        model related through *field*.
        """
        return utils.get_related_manager(cls, field)

    @classmethod
    def get_related_model(cls, field: str) -> type[models.Model]:
        """Provide shortcuts to access related model classes and managers: the model class."""
        return utils.get_related_model(cls, field)

    @classmethod
    def meta(cls) -> meta_module.Options:
        """Make ``_meta`` public in templates through a class method called ``meta``."""
        return cls._meta

    def reload(self) -> Self:
        """Provide a :meth:`reload` method to re-fetch the instance from the database."""
        return type(self)._default_manager.get(pk=self.pk)

    # --- Internals --------------------------------------------------------------------------------

    @contextlib.contextmanager
    def _assigning_changes_only(self) -> Iterator[None]:
        """Count as assigned by the block only the fields whose value it changed, raising or not."""
        assigned_fields, values = set(self._assigned_fields), dict(self.__dict__)
        try:
            yield
        finally:
            self._assigned_fields = assigned_fields | {
                name
                for name in self._assigned_fields - assigned_fields
                if not comparison.is_equal(self.__dict__[name], values.get(name, Missing))
            }

    @override
    def _do_update(
        self,
        base_qs: QuerySet,
        using: str | None,
        pk_val: Any,
        values: Collection[tuple[models.Field, type[models.Model] | None, Any]],
        update_fields: Iterable[str] | None,
        forced_update: bool,
        returning_fields: Sequence[models.Field],
    ) -> list[Sequence[Any]]:
        filtered_qs = base_qs

        # None for a save that skips save(), as loading a fixture does.
        if (save_preconditions := self._preconditions) is not None and (
            preconditions := self.get_preconditions(
                frozenset(field.name for field, _, _ in values),
                check_state=self._check_state,
                pre_excludes=save_preconditions.pre_excludes,
                pre_filters=save_preconditions.pre_filters,
            )
        ).has_lookups():
            # Each table of a row split over several is guarded through the model's queryset, which
            # reaches the fields of every table.
            if base_qs.model is self._meta.concrete_model:
                filtered_qs = preconditions.filter_queryset(base_qs)
            else:
                # fmt: off
                filtered_qs = base_qs.filter(
                    pk__in=preconditions.filter_queryset(
                        type(self)._base_manager
                        .using(using)
                        .filter(pk=pk_val)
                    )
                    .values('pk')
                )
                # fmt: on

        updated = super()._do_update(
            filtered_qs,
            using,
            pk_val,
            values,
            update_fields,
            forced_update,
            returning_fields,
        )

        # A guarded update matching no row raises, and never falls through to Django's insert.
        if not updated and filtered_qs is not base_qs:
            raise self.precondition_error_class()
        return updated

    def _get_checked_field_groups(self) -> Iterator[frozenset[str]]:
        """Yield the names of the fields each uniqueness and each constraint check names."""
        # django-stubs declares neither _get_unique_checks nor _get_expr_references, both Model's.
        # pyrefly: ignore[missing-attribute]
        unique_checks, date_checks = self._get_unique_checks(include_meta_constraints=True)
        for _model, names in unique_checks:
            yield frozenset(names)
        for _model, _lookup, name, unique_for in date_checks:
            yield frozenset((name, unique_for))

        # A parent's constraint names fields the model inherits: its own options resolve them.
        for _model, constraints in self.get_constraints():
            for constraint in constraints:
                expressions = [
                    *getattr(constraint, 'expressions', ()),
                    getattr(constraint, 'condition', None),
                ]
                references = [
                    reference
                    for expression in expressions
                    if expression is not None
                    # pyrefly: ignore[missing-attribute]
                    for reference, *_ in self._get_expr_references(expression)
                ]
                yield frozenset(
                    self._meta.pk.name
                    if reference == 'pk'
                    else self._meta.get_field(reference).name
                    for reference in (*getattr(constraint, 'fields', ()), *references)
                )

    @classmethod
    def _get_field_attnames(cls) -> frozenset[str]:
        """Return the attnames of the fields a save may write, worked out once per model class."""
        if (attnames := cls.__dict__.get('_field_attnames')) is None:
            cls._field_attnames = attnames = frozenset(
                f.attname for f in cls._meta.concrete_fields if not f.generated
            )
        return attnames

    def _get_update_fields(
        self,
        update_fields: frozenset[str] | None,
        *,
        updating: bool,
    ) -> frozenset[str] | None:
        """
        Return the fields a save given *update_fields* writes, ``None`` for every field.

        These are *update_fields*, else the fields assigned, with ``always_update_fields``, as
        :meth:`get_update_fields` returns them, without an unchanged primary key.
        """
        if update_fields is None and updating and self.track_update_fields:
            update_fields = frozenset(self._assigned_fields)
        if update_fields and self.always_update_fields:
            update_fields |= frozenset(self.always_update_fields)
        update_fields = self.get_update_fields(update_fields)

        pk_attname = self._meta.pk.attname
        if (
            updating
            and self.pk != self.previous_pk
            and (update_fields is None or pk_attname in update_fields)
        ):
            # A save of a row given a new primary key inserts a copy, as Django's does.
            return None
        return update_fields - {pk_attname} if update_fields else update_fields

    def _writes_state(self, update_fields: frozenset[str] | None) -> bool:
        """Return whether a save writing *update_fields*, ``None`` for every field, writes state."""
        return (
            self.states is not None
            and 'state' in self.__dict__
            and (update_fields is None or 'state' in update_fields)
        )


class BetterUniquenessErrorsMixin(_ModelMixin):
    """
    A model mixin raising the uniqueness errors a form shows, set up by its class attributes.

    **Use cases**

    Case: your model has some non-editable fields that are included in a uniqueness constraint.
    Issue: the uniqueness errors shown in your forms include the name of the hidden fields.
    Solution: exclude the name of the hidden fields from the error messages.
    Implementation: set ``unique_together_hide_fields`` to the name of those hidden fields.

    Case: sometimes the form submit may raise an integrity error (concurrency, [yes] crazy
    unexpected usage of Django).
    Issue: those integrity errors are unfortunately returned as Internal Server Error (HTTP 500).
    Solution: convert the uniqueness integrity errors to validation errors and return an awesome
    form with errors.
    Implementation: set ``unique_from_integrity_error`` to ``True``, and subclass
    :class:`pytoolbox.django.views.mixins.ValidationErrorsMixin` in your edit views.
    """

    #: Whether a save failing on a ``unique_together`` constraint raises a
    #: :class:`~django.core.exceptions.ValidationError` in place of the
    #: :class:`~django.db.utils.IntegrityError`.
    unique_from_integrity_error: ClassVar[bool] = True

    #: The fields left out of the ``unique_together`` errors, such as the non-editable fields a form
    #: does not show.
    unique_together_hide_fields: ClassVar[tuple[str, ...]] = ()

    @override
    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Convert uniqueness :class:`~django.db.utils.IntegrityError` to validation errors."""
        try:
            # A savepoint, to leave an outer transaction usable once the error is caught.
            with transaction.atomic(using=using or router.db_for_write(type(self), instance=self)):
                super().save(
                    force_insert=force_insert,
                    force_update=force_update,
                    using=using,
                    update_fields=update_fields,
                    **kwargs,
                )
        except IntegrityError as exc:
            if self.unique_from_integrity_error:
                match = re.search(r'duplicate key[^\)]+\((?P<fields>[^\)]+)\)', exc.args[0])
                if match:
                    fields = {
                        f.strip().replace('_id', '') for f in match.groupdict()['fields'].split(',')
                    }
                    if fields in (set(u) for u in self._meta.unique_together):
                        fields = sorted(fields - set(self.unique_together_hide_fields))
                        if fields:
                            error = self.unique_error_message(type(self), fields)
                            raise ValidationError({fields[0]: error}) if len(fields) == 1 else error
                        self._handle_hidden_duplicate_key_error(exc)
                        # The handler did not raise: the error is handled.
                        return
            raise

    def _handle_hidden_duplicate_key_error(self, exc: IntegrityError) -> None:
        raise exc

    @override
    def _perform_unique_checks(  # pyrefly: ignore[bad-override]
        self,
        unique_checks: list[tuple[type[models.Model], tuple[str, ...]]],
    ) -> dict[str, list[ValidationError]]:
        # django-stubs does not declare this private Django hook: neither @override nor the super()
        # call below is checked against it.
        # pyrefly: ignore[missing-attribute]
        errors_by_field = super()._perform_unique_checks(unique_checks)
        hidden_fields = set(self.unique_together_hide_fields)
        if not hidden_fields:
            return errors_by_field
        filtered_errors_by_field = collections.defaultdict(list)
        for field, errors in errors_by_field.items():
            for error in errors:
                # A uniqueness error over several fields is rewritten without the hidden ones.
                if len(error.params.get('unique_check', [])) > 1:
                    fields = [f for f in error.params['unique_check'] if f not in hidden_fields]
                    if fields:
                        error = self.unique_error_message(type(self), fields)
                        filtered_errors_by_field[fields[0] if len(fields) == 1 else field].append(
                            error
                        )
                else:
                    filtered_errors_by_field[field].append(error)
        return filtered_errors_by_field


@dataclass(frozen=True, slots=True)
class Preconditions:
    """The lookups a row must match for an update to write it."""

    #: The lookups the row must match none of.
    pre_excludes: dict[str, Any]

    #: The lookups the row must match all of.
    pre_filters: dict[str, Any]

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Return *queryset* limited to the rows meeting these preconditions."""
        for lookup, value in self.pre_excludes.items():
            queryset = queryset.exclude(**{lookup: value})
        return queryset.filter(**self.pre_filters)

    def has_lookups(self) -> bool:
        """Return whether a row may fail these preconditions."""
        return bool(self.pre_excludes or self.pre_filters)


# --- Internals ------------------------------------------------------------------------------------

_FETCH_MANY_CODE: Final[CodeType] = DeferredAttribute.fetch_many.__code__


__all__ = _all.diff(globals())
