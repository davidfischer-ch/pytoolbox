"""
Mix-ins for building your own models.

Recommended sub-classing order:

- BetterUniquenessErrorsMixin
- AutoForceInsertMixin
- CallFieldsPreSaveMixin
- AutoUpdateFieldsMixin
- AlwaysUpdateFieldsMixin
- AutoRemovePKFromUpdateFieldsMixin
- ValidateOnSaveMixin (will defeat the detection method of AutoUpdateFieldsMixin if put before it)
- UpdatePreconditionsMixin
- StateTransitionPreconditionMixin
- StateTransitionEventsMixin

Order for these does not matter:

- PublicMetaMixin
- RelatedModelMixin
- ReloadMixin
- SaveInstanceFilesMixin
"""
# pylint: disable=protected-access,too-few-public-methods

from __future__ import annotations

import collections
import itertools
import re
import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from django.core.exceptions import ValidationError
from django.db import DatabaseError, models
from django.db.models.fields.files import FileField
from django.db.utils import IntegrityError
from django.utils.functional import cached_property

from pytoolbox import itertools as py_itertools  # pylint:disable=reimported
from pytoolbox import module
from pytoolbox.django import signals
from pytoolbox.django.core import exceptions

from . import utils

try:
    _ModelNotUpdated: type[Exception] = models.Model.NotUpdated
except AttributeError:

    class _ModelNotUpdated(Exception):  # type: ignore[no-redef]
        """Sentinel: Django < 6 does not raise Model.NotUpdated."""


if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.db.models import options as meta_module

_all = module.All(globals())


class AlwaysUpdateFieldsMixin:
    """
    Ensure fields listed in the attribute ``self.always_update_fields`` are always updated by
    ``self.save()``. Makes the usage of ``self.save(update_fields=...)`` cleaner.
    """

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Add ``always_update_fields`` to ``update_fields`` before saving."""
        if force_update or update_fields:
            update_fields = set(update_fields or [])
            update_fields.update(self.always_update_fields)
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class AutoForceInsertMixin:
    """Automatically set ``force_insert`` based on the instance's adding state."""

    @override
    def save(
        self,
        *,
        force_insert: bool | None = None,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Set ``force_insert`` from ``_state.adding`` when not explicitly given."""
        if force_insert is None:
            force_insert = self._state.adding
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class AutoRemovePKFromUpdateFieldsMixin:
    """
    If the primary key is set but unchanged, then remove the primary key from the list of fields to
    update. This fix an issue when saving, ``ValueError: The following fields do not exist in this
    model or are m2m fields: id.``. This check is probably implemented by Django developers to
    protect from unintentional data overwrite.

    If the primary key is set to a new value, then the intention of the developer is probably to
    duplicate the model by saving it with a new primary key. So the mix-in let Django save with its
    own default options for save.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.previous_pk = self.pk

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Remove unchanged primary key from ``update_fields`` to avoid Django errors."""
        if update_fields and self._meta.pk.attname in update_fields:
            if self.pk == self.previous_pk:
                update_fields = {f for f in update_fields if f != self._meta.pk.attname}
            else:
                # This is probably the model duplication pattern
                force_insert = False
                force_update = False
                update_fields = None
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        self.previous_pk = self.pk


class AutoUpdateFieldsMixin:
    """
    Keep track of what fields were set in order to make UPDATE queries lighter.

    This mix-in comes with the following features:

    * Foreign keys and the mutable types are correctly handled.
    * Models with a primary key preset to a value before being saved in database are correctly
      handled.
    * You can specify the value for `force_update` if it is `None` with `default_force_update`.

    However this low-memory footprint mix-in also comes with some limitations, it does not:

    * Store old fields values - you cannot know if the fields are really modified or not.
    * Watch for background modifications of the mutable fields - it can drives you crazy, sometimes.
    * Detect fields updated by the field's pre_save - CallFieldsPreSaveMixin before this mix-in.
    * Filter the primary key from the list of fields to update - AutoRemovePKFromUpdateFieldsMixin
      after this mix-in.
    """

    default_force_update = False

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._setted_fields = set()
        self._fields_names = frozenset(f.attname for f in self._meta.fields)

    def __setattr__(self, name: str, value: object) -> None:
        """Track field assignments for automatic ``update_fields`` detection."""
        # Check the instance is both initialized and already stored in DB
        if name in getattr(self, '_fields_names', set()) and not self._state.adding:
            self._setted_fields.add(name)
        return super().__setattr__(name, value)

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool | None = None,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Populate ``update_fields`` from tracked field assignments."""
        if not self._state.adding and not force_insert:
            if force_update is None:
                force_update = self.default_force_update
            if update_fields is None:
                update_fields = set(self._setted_fields)
        super().save(
            force_insert=force_insert,
            force_update=bool(force_update),
            using=using,
            update_fields=update_fields,
        )
        self._setted_fields = set()


class BetterUniquenessErrorsMixin:
    """
    Hide some fields from the unique-together errors.
    Convert uniqueness integrity errors to validation errors.

    **Use cases**

    Case: Your model have some non editable fields that are included in a uniqueness constraint.
    Issue: The uniqueness errors shown in your forms includes the name of the hidden fields.
    Solution: Exclude the name of the hidden fields from the error messages.
    Implementation: Set `unique_together_hide_fields` to the name of those hidden fields.

    Case: Sometimes the form submit may raise an integrity error (concurrency, [yes] crazy
          unexpected usage of Django).
    Issue: Those integrity errors are unfortunately returned as Internal Server Error (HTTP 500).
    Solution: Convert the uniqueness integrity errors to validation errors and return an awesome
              form with errors.
    Implementation: Set `unique_from_integrity_error` to True. And subclass
    :class:`pytoolbox.django.views.mixins.ValidationErrorsMixin` in your edit views.
    """

    unique_from_integrity_error = True
    unique_together_hide_fields = ()

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Convert uniqueness :class:`~django.db.utils.IntegrityError` to validation errors."""
        try:
            super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
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
                        return  # handler didn't raise; treat as handled
            raise

    def _handle_hidden_duplicate_key_error(self, exc: IntegrityError) -> None:
        raise exc

    @override
    def _perform_unique_checks(self, unique_checks: list) -> dict[str, list]:
        errors_by_field = super()._perform_unique_checks(unique_checks)
        hidden_fields = set(self.unique_together_hide_fields)
        if not hidden_fields:
            return errors_by_field
        filtered_errors_by_field = collections.defaultdict(list)
        for field, errors in errors_by_field.items():
            for error in errors:
                # only process the uniqueness errors related to multiple fields
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


class CallFieldsPreSaveMixin:
    """
    If you wanna be sure the fields pre_save method are called, now you can!

    For more information see: https://code.djangoproject.com/ticket/25363
    """

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Call each non-PK field's :meth:`pre_save` before saving."""
        non_pk_fields = (f for f in self._meta.local_concrete_fields if not f.primary_key)
        for field in non_pk_fields:
            field.pre_save(self, self._state.adding)
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class PublicMetaMixin:
    """
    Make `_meta` public in templates through a class method called `meta`.
    """

    @classmethod
    def meta(cls) -> meta_module.Options:
        """Return the model's ``_meta`` options for use in templates."""
        return cls._meta


class RelatedModelMixin:
    """Provide shortcuts to access related model classes and managers."""

    @classmethod
    def get_related_manager(cls, field: str) -> models.Manager:
        """Return the default manager for the model related through *field*."""
        return utils.get_related_manager(cls, field)

    @classmethod
    def get_related_model(cls, field: str) -> type[models.Model]:
        """Return the model class related through *field*."""
        return utils.get_related_model(cls, field)


class ReloadMixin:
    """Provide a :meth:`reload` method to re-fetch the instance from the database."""

    def reload(self) -> models.Model:
        """Return a fresh copy of this instance from the database."""
        return self._meta.model._default_manager.get(pk=self.pk)


class SaveInstanceFilesMixin:
    """
    Overrides saves() with a method that saves the instance first and then the instance's file
    fields this ensure that the upload_path method will get a valid instance id / private key.
    """

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Save the instance before file fields so ``upload_to`` gets a valid PK."""
        saved_fields = {}
        if self.pk is None:
            for field in self._meta.fields:
                if isinstance(field, FileField):
                    saved_fields[field.name] = getattr(self, field.name)
                    setattr(self, field.name, None)
            super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )
            for name, value in saved_fields.items():
                setattr(self, name, value)
            force_insert = False  # Do not force because we already saved the instance
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class UpdatePreconditionsMixin:
    """Guard row updates with filter/exclude preconditions for optimistic concurrency."""

    precondition_error_class = exceptions.DatabaseUpdatePreconditionsError

    def apply_preconditions(
        self,
        base_qs: QuerySet,
        using: str,
        pk_val: object,
        values: list,
        update_fields: set | None,
        force_update: bool,
    ) -> tuple[QuerySet, str, object, list, set | None, bool]:
        """Apply stored precondition filters to the update query set."""
        if hasattr(self, '_preconditions'):
            pre_excludes, pre_filters = self._preconditions
            del self._preconditions
            if pre_excludes:
                base_qs = base_qs.exclude(**pre_excludes)
            if pre_filters:
                base_qs = base_qs.filter(**pre_filters)
        return base_qs, using, pk_val, values, update_fields, force_update

    def pop_preconditions(self, *args: object, **kwargs: object) -> tuple[tuple, dict, bool]:
        """Extract ``pre_excludes`` and ``pre_filters`` from *kwargs*."""
        self._preconditions = kwargs.pop('pre_excludes', {}), kwargs.pop('pre_filters', {})
        return args, kwargs, any(self._preconditions)

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
        **extra_kwargs: object,
    ) -> None:
        """Save with precondition guards, raising on failed preconditions."""
        _, _, has_preconditions = self.pop_preconditions(**extra_kwargs)
        try:
            super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )
        except _ModelNotUpdated:
            if has_preconditions:
                raise self.precondition_error_class()
            raise
        except DatabaseError as exc:
            if has_preconditions and 'did not affect' in str(exc):
                raise self.precondition_error_class()
            raise

    @override
    def _do_update(
        self,
        base_qs: QuerySet,
        using: str,
        pk_val: object,
        values: list,
        update_fields: set | None,
        force_update: bool,
        returning_fields: object,
    ) -> bool:
        # FIXME _do_update is called once for each model in the inheritance hierarchy: Handle this!
        args = self.apply_preconditions(base_qs, using, pk_val, values, update_fields, force_update)
        updated = super()._do_update(*args, returning_fields)
        if not updated and args[0] != base_qs and base_qs.filter(pk=pk_val).exists():
            raise self.precondition_error_class()
        return updated


class StateTransitionEventsMixin:
    """Send :data:`~pytoolbox.django.signals.post_state_transition` after state changes."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.previous_state = self.state

    def on_post_state_transition(self, args: tuple, kwargs: dict) -> None:
        """Fire the post-state-transition signal with the previous state."""
        signals.post_state_transition.send(
            instance=self,
            previous_state=self.previous_state,
            args=args,
            kwargs=kwargs,
        )

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
    ) -> None:
        """Save and fire post-state-transition signal if state was updated."""
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if 'state' in (update_fields or ['state']):
            self.on_post_state_transition((), {'update_fields': update_fields})
            self.previous_state = self.state


class StateTransitionPreconditionMixin(UpdatePreconditionsMixin):
    """Add state-based preconditions to row updates for safe transitions."""

    check_state = True
    invalid_state_error_class = exceptions.InvalidStateError
    transition_not_allowed_error_class = exceptions.TransitionNotAllowedError

    def can_transit_to(self, state: str, fail: bool = False, noop_skip: bool = False) -> bool:
        """
        Return a value depending on whether the transition to `state` is allowed.

        * True if transition to `state` is allowed.
        * False if `fail` is set to False or `noop_skip` is set to True and state is unchanged.
        * Else raise a transition not allowed error.
        """
        if state in self.states.TRANSITIONS[self.state]:
            return True
        if not fail or noop_skip and self.state == state:
            return False
        raise self.transition_not_allowed_error_class(instance=self, state=state)

    def check_state_in(self, states: object, fail: bool = False) -> bool:
        """Return ``True`` if the instance's state is in *states*."""
        states = sorted(py_itertools.chain(states))
        if self.state in states:
            return True
        if not fail:
            return False
        raise self.invalid_state_error_class(instance=self, states=states)

    def pop_preconditions(self, *args: object, **kwargs: object) -> tuple[tuple, dict, bool]:
        """
        Add state precondition if state will be saved and state is not enforced by preconditions.
        """
        args, kwargs, _ = super().pop_preconditions(*args, **kwargs)
        if kwargs.pop('check_state', self.check_state) and 'state' in kwargs.get(
            'update_fields', ['state']
        ):
            pre_excludes, pre_filters = self._preconditions
            if not any(f.startswith('state') for f in itertools.chain(pre_excludes, pre_filters)):
                states, valid = self.states.get_transit_from(self.state, auto_inverse=True)
                assert states, (states, valid)
                key, values = (
                    ('state__in', states) if len(states) > 1 else ('state', next(iter(states)))
                )
                (pre_filters if valid else pre_excludes)[key] = values
        return args, kwargs, any(self._preconditions)


class ValidateOnSaveMixin:
    """Run :meth:`full_clean` automatically before every save."""

    validate_on_save = True
    validate_on_save_kwargs = {}
    """Keyword arguments forwarded to :meth:`full_clean`."""

    @override
    def save(
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: object = None,
        **extra_kwargs: object,
    ) -> None:
        """Call :meth:`full_clean` before saving if ``validate_on_save`` is set."""
        validate = extra_kwargs.pop('validate', None)
        if validate if validate is not None else self.validate_on_save:
            self.full_clean(**self.validate_on_save_kwargs)
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class FasterValidateOnSaveMixin(ValidateOnSaveMixin):
    """
    Do not validate uniqueness nor relation fields on save to prevent excessive SELECT queries.
    """

    @cached_property
    def validate_on_save_kwargs(self) -> dict[str, object]:
        """Return kwargs that skip uniqueness and relation field validation."""
        return {
            'exclude': [f.name for f in self._meta.concrete_fields if f.is_relation],
            'validate_unique': False,
        }


__all__ = _all.diff(globals())
