# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own models.

Recommended sub-classing order:

- BetterUniquenessErrorsMixin
- AutoForceInsertMixin
- CallFieldsPreSaveMixin
- AutoUpdateFieldsMixin
- AlwaysUpdateFieldsMixin
- AutoRemovePKFromUpdateFieldsMixin
- ValidateOnSaveMixin (will defeat the detection method of AutoUpdateFieldsMixin if placed before it)
- UpdatePreconditionsMixin
- StateTransitionPreconditionMixin
- StateTransitionEventsMixin

Order for these does not matter:

- PublicMetaMixin
- RelatedModelMixin
- ReloadMixin
- SaveInstanceFilesMixin
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, itertools, re

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models.fields.files import FileField
from django.db.utils import IntegrityError
from django.utils.functional import cached_property

from pytoolbox.django import signals
from pytoolbox.django.core import exceptions
from pytoolbox import itertools as py_itertools, module  # pylint:disable=reimported

from . import utils

_all = module.All(globals())


class AlwaysUpdateFieldsMixin(object):
    """
    Ensure fields listed in the attribute ``self.always_update_fields`` are always updated by
    ``self.save()``. Makes the usage of ``self.save(update_fields=...)`` cleaner.
    """
    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if kwargs.get('force_update') or update_fields:
            update_fields = set(update_fields or [])
            update_fields.update(self.always_update_fields)
            kwargs['update_fields'] = update_fields
        super(AlwaysUpdateFieldsMixin, self).save(*args, **kwargs)


class AutoForceInsertMixin(object):

    def save(self, *args, **kwargs):
        if kwargs.get('force_insert') is None:
            kwargs['force_insert'] = self._state.adding
        super(AutoForceInsertMixin, self).save(*args, **kwargs)


class AutoRemovePKFromUpdateFieldsMixin(object):
    """
    If the primary key is set but unchanged, then remove the primary key from the list of fields to
    update. This fix an issue when saving, ``ValueError: The following fields do not exist in this
    model or are m2m fields: id.``. This check is probably implemented by Django developers to
    protect from unintentional data overwrite.

    If the primary key is set to a new value, then the intention of the developer is probably to
    duplicate the model by saving it with a new primary key. So the mix-in let Django save with its
    own default options for save.
    """
    def __init__(self, *args, **kwargs):
        super(AutoRemovePKFromUpdateFieldsMixin, self).__init__(*args, **kwargs)
        self.previous_pk = self.pk

    def save(self, **kwargs):
        update_fields = kwargs.get('update_fields')
        if update_fields and self._meta.pk.attname in update_fields:
            if self.pk == self.previous_pk:
                kwargs['update_fields'] = {f for f in update_fields if f != self._meta.pk.attname}
            else:
                # This is probably the model duplication pattern
                for argument in 'force_insert', 'force_update', 'update_fields':
                    kwargs.pop(argument, None)
        super(AutoRemovePKFromUpdateFieldsMixin, self).save(**kwargs)
        self.previous_pk = self.pk


class AutoUpdateFieldsMixin(object):
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

    def __init__(self, *args, **kwargs):
        super(AutoUpdateFieldsMixin, self).__init__(*args, **kwargs)
        self._setted_fields = set()
        self._fields_names = frozenset(f.attname for f in self._meta.fields)

    def __setattr__(self, name, value):
        # Check the instance is both initialized and already stored in DB
        if name in getattr(self, '_fields_names', set()) and not self._state.adding:
            self._setted_fields.add(name)
        return super(AutoUpdateFieldsMixin, self).__setattr__(name, value)

    def save(self, *args, **kwargs):
        if not self._state.adding and not kwargs.get('force_insert'):
            if kwargs.get('force_update') is None:
                kwargs['force_update'] = self.default_force_update
            if kwargs.get('update_fields') is None:
                kwargs['update_fields'] = set(self._setted_fields)
        super(AutoUpdateFieldsMixin, self).save(*args, **kwargs)
        self._setted_fields = set()


class BetterUniquenessErrorsMixin(object):
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
    Issue: Those integrity errors are unfortunately returned as Internal Server Error (HTTP 500 page).
    Solution: Convert the uniqueness integrity errors to validation errors and return an awesome
              form with errors.
    Implementation: Set `unique_from_integrity_error` to True. And subclass
    :class:`pytoolbox.django.views.mixins.ValidationErrorsMixin` in your edit views.
    """
    unique_from_integrity_error = True
    unique_together_hide_fields = ()

    def save(self, *args, **kwargs):
        try:
            super(BetterUniquenessErrorsMixin, self).save(*args, **kwargs)
        except IntegrityError as e:
            if self.unique_from_integrity_error:
                match = re.search(r'duplicate key[^\)]+\((?P<fields>[^\)]+)\)', e.args[0])
                if match:
                    fields = {
                        f.strip().replace('_id', '')
                        for f in match.groupdict()['fields'].split(',')
                    }
                    if fields in (set(u) for u in self._meta.unique_together):
                        fields = sorted(fields - set(self.unique_together_hide_fields))
                        if fields:
                            error = self.unique_error_message(self.__class__, fields)
                            raise ValidationError({fields[0]: error}) if len(fields) == 1 else error
                        return self._handle_hidden_duplicate_key_error(e)
            raise

    def _handle_hidden_duplicate_key_error(self, e):
        raise e

    def _perform_unique_checks(self, unique_checks):
        errors_by_field = super(BetterUniquenessErrorsMixin, self)._perform_unique_checks(
            unique_checks)

        hidden_fields = set(self.unique_together_hide_fields)
        if not hidden_fields:
            return errors_by_field
        filtered_errors_by_field = collections.defaultdict(list)
        for field, errors in errors_by_field.iteritems():
            for error in errors:
                # only process the uniqueness errors related to multiple fields
                if len(error.params.get('unique_check', [])) > 1:
                    fields = [f for f in error.params['unique_check'] if f not in hidden_fields]
                    if fields:
                        error = self.unique_error_message(self.__class__, fields)
                        filtered_errors_by_field[
                            fields[0] if len(fields) == 1 else field
                        ].append(error)
                else:
                    filtered_errors_by_field[field].append(error)
        return filtered_errors_by_field


class CallFieldsPreSaveMixin(object):
    """
    If you wanna be sure the fields pre_save method are called, now you can!

    For more information see: https://code.djangoproject.com/ticket/25363
    """
    def save(self, *args, **kwargs):
        non_pk_fields = (f for f in self._meta.local_concrete_fields if not f.primary_key)
        for field in non_pk_fields:
            field.pre_save(self, self._state.adding)
        super(CallFieldsPreSaveMixin, self).save(*args, **kwargs)


class PublicMetaMixin(object):
    """
    Make `_meta` public in templates through a class method called `meta`.
    """
    @classmethod
    def meta(cls):
        return cls._meta


class RelatedModelMixin(object):

    @classmethod
    def get_related_manager(cls, field):
        return utils.get_related_manager(cls, field)

    @classmethod
    def get_related_model(cls, field):
        return utils.get_related_model(cls, field)


class ReloadMixin(object):

    def reload(self):
        return self._meta.model._default_manager.get(pk=self.pk)


class SaveInstanceFilesMixin(object):
    """
    Overrides saves() with a method that saves the instance first and then the instance's file
    fields this ensure that the upload_path method will get a valid instance id / private key.
    """
    def save(self, *args, **kwargs):
        saved_fields = {}
        if self.pk is None:
            for field in self._meta.fields:
                if isinstance(field, FileField):
                    saved_fields[field.name] = getattr(self, field.name)
                    setattr(self, field.name, None)
            super(SaveInstanceFilesMixin, self).save(*args, **kwargs)
            for name, value in saved_fields.iteritems():
                setattr(self, name, value)
            kwargs['force_insert'] = False  # Do not force because we already saved the instance
        super(SaveInstanceFilesMixin, self).save(*args, **kwargs)


class UpdatePreconditionsMixin(object):

    precondition_error_class = exceptions.DatabaseUpdatePreconditionsError

    def apply_preconditions(self, base_qs, using, pk_val, values, update_fields, force_update):
        if hasattr(self, '_preconditions'):
            pre_excludes, pre_filters = self._preconditions
            del self._preconditions
            if pre_excludes:
                base_qs = base_qs.exclude(**pre_excludes)
            if pre_filters:
                base_qs = base_qs.filter(**pre_filters)
        return base_qs, using, pk_val, values, update_fields, force_update

    def pop_preconditions(self, *args, **kwargs):
        self._preconditions = kwargs.pop('pre_excludes', {}), kwargs.pop('pre_filters', {})
        return args, kwargs, any(self._preconditions)

    def save(self, *args, **kwargs):
        args, kwargs, has_preconditions = self.pop_preconditions(*args, **kwargs)
        try:
            super(UpdatePreconditionsMixin, self).save(*args, **kwargs)
        except DatabaseError as e:
            if has_preconditions and 'did not affect' in '{0}'.format(e):
                raise self.precondition_error_class()
            raise

    def _do_update(self, base_qs, using, pk_val, values, update_fields, force_update):
        # FIXME _do_update is called once for each model in the inheritance hierarchy: Handle this!
        args = self.apply_preconditions(base_qs, using, pk_val, values, update_fields, force_update)
        updated = super(UpdatePreconditionsMixin, self)._do_update(*args)
        if not updated and args[0] != base_qs and base_qs.filter(pk=pk_val).exists():
            raise self.precondition_error_class()
        return updated


class StateTransitionEventsMixin(object):

    def __init__(self, *args, **kwargs):
        super(StateTransitionEventsMixin, self).__init__(*args, **kwargs)
        self.previous_state = self.state

    def on_post_state_transition(self, args, kwargs):
        signals.post_state_transition.send(
            instance=self, previous_state=self.previous_state, args=args, kwargs=kwargs)

    def save(self, *args, **kwargs):
        super(StateTransitionEventsMixin, self).save(*args, **kwargs)
        if 'state' in kwargs.get('update_fields', ['state']):
            self.on_post_state_transition(args, kwargs)
            self.previous_state = self.state


class StateTransitionPreconditionMixin(UpdatePreconditionsMixin):

    check_state = True
    invalid_state_error_class = exceptions.InvalidStateError
    transition_not_allowed_error_class = exceptions.TransitionNotAllowedError

    def can_transit_to(self, state, fail=False, noop_skip=False):
        """
        Helper that return the following:

        * True if transition to `state` is allowed.
        * False if `fail` is set to False or `noop_skip` is set to True and state is unchanged.
        * Else raise a transition not allowed error.
        """
        if state in self.states.TRANSITIONS[self.state]:
            return True
        if not fail or noop_skip and self.state == state:
            return False
        raise self.transition_not_allowed_error_class(instance=self, state=state)

    def check_state_in(self, states, fail=False):
        states = sorted(py_itertools.chain(states))
        if self.state in states:
            return True
        if not fail:
            return False
        raise self.invalid_state_error_class(instance=self, states=states)

    def pop_preconditions(self, *args, **kwargs):
        """
        Add state precondition if state will be saved and state is not enforced by preconditions.
        """
        args, kwargs, has_preconditions = \
            super(StateTransitionPreconditionMixin, self).pop_preconditions(*args, **kwargs)
        if (
            kwargs.pop('check_state', self.check_state) and
            'state' in kwargs.get('update_fields', ['state'])
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


class ValidateOnSaveMixin(object):

    validate_on_save = True
    validate_on_save_kwargs = {}

    def save(self, *args, **kwargs):
        if kwargs.pop('validate', self.validate_on_save):
            self.full_clean(**self.validate_on_save_kwargs)
        super(ValidateOnSaveMixin, self).save(*args, **kwargs)


class FasterValidateOnSaveMixin(ValidateOnSaveMixin):
    """
    Do not validate uniqueness nor relation fields on save to prevent excessive SELECT queries.
    """

    @cached_property
    def validate_on_save_kwargs(self):
        return {
            'exclude': [f.name for f in self._meta.concrete_fields if f.rel],
            'validate_unique': False
        }


__all__ = _all.diff(globals())
