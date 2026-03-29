# pylint:disable=unused-argument
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, models
from django.db.models.fields.files import FileField
from django.db.utils import IntegrityError

from pytoolbox.django.core import exceptions
from pytoolbox.django.models import mixins

# ---------------------------------------------------------------------------
# FasterValidateOnSaveMixin
# ---------------------------------------------------------------------------


def test_faster_validate_on_save_mixin_uses_is_relation() -> None:
    """Relation fields are excluded from validation, regular fields are not."""

    class TestModel(mixins.FasterValidateOnSaveMixin, models.Model):
        name = models.CharField(max_length=100)
        other = models.ForeignKey(
            'auth.User',
            on_delete=models.CASCADE,
            null=True,
        )

        class Meta:
            app_label = 'test'

    instance = TestModel.__new__(TestModel)
    kwargs = instance.validate_on_save_kwargs
    assert 'other' in kwargs['exclude']
    assert 'name' not in kwargs['exclude']


# ---------------------------------------------------------------------------
# PublicMetaMixin
# ---------------------------------------------------------------------------


def test_public_meta_mixin() -> None:
    """meta() classmethod exposes the private _meta for use in templates."""

    class TestModel(mixins.PublicMetaMixin, models.Model):
        class Meta:
            app_label = 'test'

    assert TestModel.meta() is TestModel._meta  # pylint:disable=no-member


# ---------------------------------------------------------------------------
# ValidateOnSaveMixin
# ---------------------------------------------------------------------------


def test_validate_on_save_mixin_calls_full_clean() -> None:
    """save() calls full_clean() when validate_on_save is True (default)."""

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class TestObj(mixins.ValidateOnSaveMixin, Base):
        full_clean = MagicMock()

    obj = TestObj()
    obj.save()
    obj.full_clean.assert_called_once_with()


def test_validate_on_save_mixin_skips_when_disabled() -> None:
    """save() skips full_clean() when validate_on_save is set to False."""

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class TestObj(mixins.ValidateOnSaveMixin, Base):
        validate_on_save = False
        full_clean = MagicMock()

    obj = TestObj()
    obj.save()
    obj.full_clean.assert_not_called()


def test_validate_on_save_mixin_skips_via_kwarg() -> None:
    """save(validate=False) bypasses full_clean() even if default is True."""

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class TestObj(mixins.ValidateOnSaveMixin, Base):
        full_clean = MagicMock()

    obj = TestObj()
    obj.save(validate=False)
    obj.full_clean.assert_not_called()


# ---------------------------------------------------------------------------
# AlwaysUpdateFieldsMixin
# ---------------------------------------------------------------------------


def test_always_update_fields_mixin() -> None:
    """always_update_fields are injected into update_fields when saving."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AlwaysUpdateFieldsMixin, Base):
        always_update_fields = ('modified_at',)

    obj = TestObj()
    obj.save(update_fields=['name'])
    assert 'modified_at' in saved_kwargs['update_fields']
    assert 'name' in saved_kwargs['update_fields']


def test_always_update_fields_mixin_no_update_fields() -> None:
    """Without update_fields, always_update_fields does not force a partial."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AlwaysUpdateFieldsMixin, Base):
        always_update_fields = ('modified_at',)

    obj = TestObj()
    obj.save()
    assert 'update_fields' not in saved_kwargs


def test_always_update_fields_mixin_force_update() -> None:
    """force_update=True also triggers always_update_fields injection."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AlwaysUpdateFieldsMixin, Base):
        always_update_fields = ('modified_at',)

    obj = TestObj()
    obj.save(force_update=True)
    assert 'modified_at' in saved_kwargs['update_fields']


# ---------------------------------------------------------------------------
# AutoForceInsertMixin
# ---------------------------------------------------------------------------


def test_auto_force_insert_mixin() -> None:
    """force_insert is set from _state.adding when not explicitly provided."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AutoForceInsertMixin, Base):
        _state = MagicMock(adding=True)

    obj = TestObj()
    obj.save()
    assert saved_kwargs['force_insert'] is True

    saved_kwargs.clear()
    obj._state.adding = False
    obj.save()
    assert saved_kwargs['force_insert'] is False


def test_auto_force_insert_mixin_explicit_override() -> None:
    """Explicit force_insert=False is not overridden by _state.adding."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AutoForceInsertMixin, Base):
        _state = MagicMock(adding=True)

    obj = TestObj()
    obj.save(force_insert=False)
    assert saved_kwargs['force_insert'] is False


# ---------------------------------------------------------------------------
# CallFieldsPreSaveMixin
# ---------------------------------------------------------------------------


def test_call_fields_pre_save_mixin() -> None:
    """pre_save is called on all non-pk fields, pk field is skipped."""
    field1 = MagicMock(primary_key=False)
    field2 = MagicMock(primary_key=True)
    field3 = MagicMock(primary_key=False)

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class TestObj(mixins.CallFieldsPreSaveMixin, Base):
        _meta = MagicMock(local_concrete_fields=[field1, field2, field3])
        _state = MagicMock(adding=False)

    obj = TestObj()
    obj.save()
    field1.pre_save.assert_called_once_with(obj, False)
    field2.pre_save.assert_not_called()
    field3.pre_save.assert_called_once_with(obj, False)


# ---------------------------------------------------------------------------
# ReloadMixin
# ---------------------------------------------------------------------------


def test_reload_mixin() -> None:
    """reload() fetches a fresh instance from the default manager by pk."""
    mock_instance = MagicMock()

    class TestObj(mixins.ReloadMixin):
        pk = 42
        _meta = MagicMock()

    TestObj._meta.model._default_manager.get.return_value = mock_instance
    obj = TestObj()
    result = obj.reload()
    TestObj._meta.model._default_manager.get.assert_called_once_with(pk=42)
    assert result is mock_instance


# ---------------------------------------------------------------------------
# AutoRemovePKFromUpdateFieldsMixin
# ---------------------------------------------------------------------------


def _make_auto_remove_pk_obj(pk_value=1):
    """Create a test object for AutoRemovePKFromUpdateFieldsMixin."""
    saved_kwargs = {}

    class Base:
        def __init__(self):
            self.pk = pk_value
            self._meta = MagicMock()
            self._meta.pk.attname = 'id'

        def save(self, **kwargs):
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AutoRemovePKFromUpdateFieldsMixin, Base):
        pass

    return TestObj(), saved_kwargs


def test_auto_remove_pk_unchanged_pk_removed() -> None:
    """Unchanged PK is removed from update_fields to avoid Django error."""
    obj, saved_kwargs = _make_auto_remove_pk_obj(pk_value=1)
    obj.save(update_fields={'id', 'name'})
    assert 'id' not in saved_kwargs['update_fields']
    assert 'name' in saved_kwargs['update_fields']


def test_auto_remove_pk_changed_pk_clears_args() -> None:
    """Changed PK triggers duplication pattern: force_insert etc removed."""
    obj, saved_kwargs = _make_auto_remove_pk_obj(pk_value=1)
    obj.pk = 999  # Simulate changing PK for duplication
    obj.save(
        update_fields={'id', 'name'},
        force_insert=True,
        force_update=False,
    )
    assert 'force_insert' not in saved_kwargs
    assert 'force_update' not in saved_kwargs
    assert 'update_fields' not in saved_kwargs


def test_auto_remove_pk_updates_previous_pk_after_save() -> None:
    """previous_pk is updated to current pk after a successful save."""
    obj, _ = _make_auto_remove_pk_obj(pk_value=1)
    assert obj.previous_pk == 1
    obj.pk = 2
    obj.save(update_fields={'id'})
    assert obj.previous_pk == 2


def test_auto_remove_pk_no_update_fields() -> None:
    """Without update_fields the mixin does nothing special."""
    obj, saved_kwargs = _make_auto_remove_pk_obj(pk_value=1)
    obj.save()
    # update_fields not in kwargs so the branch is skipped
    assert 'update_fields' not in saved_kwargs


# ---------------------------------------------------------------------------
# AutoUpdateFieldsMixin
# ---------------------------------------------------------------------------


def _make_auto_update_obj(adding=False):
    """Create a test object for AutoUpdateFieldsMixin."""
    saved_kwargs = {}

    class Base:
        def __init__(self):
            self._state = MagicMock(adding=adding)
            self._meta = MagicMock()
            field_name = MagicMock(attname='name')
            field_status = MagicMock(attname='status')
            self._meta.fields = [field_name, field_status]

        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AutoUpdateFieldsMixin, Base):
        pass

    return TestObj(), saved_kwargs


def test_auto_update_fields_tracks_setattr() -> None:
    """Fields set via __setattr__ are tracked for update_fields."""
    obj, saved_kwargs = _make_auto_update_obj(adding=False)
    obj.name = 'new value'
    obj.save()
    assert 'name' in saved_kwargs['update_fields']


def test_auto_update_fields_resets_after_save() -> None:
    """Tracked fields are cleared after save."""
    obj, _ = _make_auto_update_obj(adding=False)
    obj.name = 'new value'
    obj.save()
    assert obj._setted_fields == set()


def test_auto_update_fields_skips_adding() -> None:
    """When _state.adding is True, update_fields is not auto-populated."""
    obj, saved_kwargs = _make_auto_update_obj(adding=True)
    obj.name = 'new value'
    obj.save()
    assert 'update_fields' not in saved_kwargs


def test_auto_update_fields_default_force_update() -> None:
    """force_update defaults to default_force_update when not given."""
    obj, saved_kwargs = _make_auto_update_obj(adding=False)
    obj.save()
    assert saved_kwargs['force_update'] is False


def test_auto_update_fields_force_insert_skips() -> None:
    """force_insert=True bypasses auto update_fields detection."""
    obj, saved_kwargs = _make_auto_update_obj(adding=False)
    obj.name = 'changed'
    obj.save(force_insert=True)
    assert 'update_fields' not in saved_kwargs


# ---------------------------------------------------------------------------
# BetterUniquenessErrorsMixin
# ---------------------------------------------------------------------------


def _make_uniqueness_obj(
    unique_from_integrity_error=True,
    unique_together_hide_fields=(),
):
    """Create a test object for BetterUniquenessErrorsMixin."""

    class Base:
        def save(self, *args, **kwargs):
            pass

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_from_integrity_error = unique_from_integrity_error
    obj.unique_together_hide_fields = unique_together_hide_fields
    obj._meta = MagicMock()
    return obj


def test_uniqueness_save_converts_integrity_error() -> None:
    """IntegrityError with duplicate key is converted to ValidationError."""

    class Base:
        def save(self, *args, **kwargs):
            raise IntegrityError(
                'duplicate key value violates unique (name)',
            )

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj._meta = MagicMock()
    obj._meta.unique_together = [('name',)]
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ()
    mock_error = ValidationError('unique error')
    obj.unique_error_message = MagicMock(return_value=mock_error)

    with pytest.raises(ValidationError):
        obj.save()


def test_uniqueness_save_reraises_non_matching_integrity() -> None:
    """IntegrityError without duplicate key pattern is re-raised as-is."""

    class Base:
        def save(self, *args, **kwargs):
            raise IntegrityError('some other error')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ()

    with pytest.raises(IntegrityError, match='some other error'):
        obj.save()


def test_uniqueness_save_disabled() -> None:
    """When unique_from_integrity_error is False, IntegrityError is raised."""

    class Base:
        def save(self, *args, **kwargs):
            raise IntegrityError('duplicate key value (name, org)')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_from_integrity_error = False
    obj.unique_together_hide_fields = ()

    with pytest.raises(IntegrityError):
        obj.save()


def test_uniqueness_hidden_fields_calls_handler() -> None:
    """When all fields are hidden, _handle_hidden_duplicate_key_error is called."""

    class Base:
        def save(self, *args, **kwargs):
            raise IntegrityError('duplicate key value (org)')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj._meta = MagicMock()
    obj._meta.unique_together = [('org',)]
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ('org',)
    obj._handle_hidden_duplicate_key_error = MagicMock()
    obj.save()
    obj._handle_hidden_duplicate_key_error.assert_called_once()


def test_perform_unique_checks_hides_fields() -> None:
    """_perform_unique_checks filters hidden fields from error messages."""
    error = MagicMock()
    error.params = {'unique_check': ['org', 'name']}

    class Base:
        def _perform_unique_checks(self, unique_checks):  # pylint:disable=unused-argument
            return {'__all__': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_together_hide_fields = ('org',)
    obj.unique_error_message = MagicMock(return_value=MagicMock())

    result = obj._perform_unique_checks([])
    # Error should be remapped to the remaining field 'name'
    assert 'name' in result
    obj.unique_error_message.assert_called_once()


def test_perform_unique_checks_no_hidden() -> None:
    """Without hidden fields, _perform_unique_checks returns errors as-is."""
    error = MagicMock()
    error.params = {'unique_check': ['name']}

    class Base:
        def _perform_unique_checks(self, unique_checks):
            return {'name': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_together_hide_fields = ()
    result = obj._perform_unique_checks([])
    assert result == {'name': [error]}


def test_perform_unique_checks_single_field_error_passthrough() -> None:
    """Single-field unique check errors pass through even with hidden set."""
    error = MagicMock()
    error.params = {'unique_check': ['name']}

    class Base:
        def _perform_unique_checks(self, unique_checks):
            return {'name': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        pass

    obj = TestObj()
    obj.unique_together_hide_fields = ('org',)
    result = obj._perform_unique_checks([])
    assert 'name' in result
    assert error in result['name']


# ---------------------------------------------------------------------------
# SaveInstanceFilesMixin
# ---------------------------------------------------------------------------


def test_save_instance_files_new_instance() -> None:
    """File fields are cleared, instance saved, then files re-set and saved."""
    save_calls = []

    class Base:
        def save(self, *args, **kwargs):
            save_calls.append(dict(kwargs))

    file_field = MagicMock(spec=FileField)
    file_field.name = 'document'

    class TestObj(mixins.SaveInstanceFilesMixin, Base):
        pk = None
        _meta = MagicMock(fields=[file_field])
        document = 'my_file.pdf'

    obj = TestObj()
    obj.save()
    # Should have been saved twice: once without file, once with
    assert len(save_calls) == 2
    assert save_calls[1].get('force_insert') is False


def test_save_instance_files_existing_instance() -> None:
    """Existing instance (pk set) is saved once without clearing files."""
    save_calls = []

    class Base:
        def save(self, *args, **kwargs):
            save_calls.append(dict(kwargs))

    file_field = MagicMock(spec=FileField)
    file_field.name = 'document'

    class TestObj(mixins.SaveInstanceFilesMixin, Base):
        pk = 42
        _meta = MagicMock(fields=[file_field])
        document = 'my_file.pdf'

    obj = TestObj()
    obj.save()
    assert len(save_calls) == 1


# ---------------------------------------------------------------------------
# UpdatePreconditionsMixin
# ---------------------------------------------------------------------------


def _make_preconditions_obj():
    """Create a test object for UpdatePreconditionsMixin."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):
            saved_kwargs.update(kwargs)

        def _do_update(self, base_qs, using, pk_val, values, uf, fu):
            return True

    class TestObj(mixins.UpdatePreconditionsMixin, Base):
        pass

    return TestObj(), saved_kwargs


def test_pop_preconditions_extracts_kwargs() -> None:
    """pop_preconditions extracts pre_excludes and pre_filters from kwargs."""
    obj, _ = _make_preconditions_obj()
    _args, kwargs, has = obj.pop_preconditions(
        pre_excludes={'status': 'deleted'},
        pre_filters={'active': True},
        other='value',
    )
    assert has is True
    assert kwargs == {'other': 'value'}
    assert obj._preconditions == ({'status': 'deleted'}, {'active': True})


def test_pop_preconditions_empty() -> None:
    """pop_preconditions with no precondition kwargs returns has=False."""
    obj, _ = _make_preconditions_obj()
    _args, _kwargs, has = obj.pop_preconditions(name='test')
    assert has is False


def test_apply_preconditions_filters_queryset() -> None:
    """apply_preconditions applies filter and exclude to the base queryset."""
    obj, _ = _make_preconditions_obj()
    obj._preconditions = ({'status': 'deleted'}, {'active': True})
    base_qs = MagicMock()
    filtered_qs = MagicMock()
    base_qs.exclude.return_value = filtered_qs

    obj.apply_preconditions(
        base_qs,
        'default',
        1,
        [],
        None,
        False,
    )
    base_qs.exclude.assert_called_once_with(status='deleted')
    filtered_qs.filter.assert_called_once_with(active=True)
    assert not hasattr(obj, '_preconditions')


def test_apply_preconditions_no_preconditions() -> None:
    """apply_preconditions without stored preconditions passes qs through."""
    obj, _ = _make_preconditions_obj()
    base_qs = MagicMock()
    result = obj.apply_preconditions(
        base_qs,
        'default',
        1,
        [],
        None,
        False,
    )
    assert result[0] is base_qs


def test_update_preconditions_save_catches_database_error() -> None:
    """Save raises precondition error when DB error contains 'did not affect'."""

    class Base:
        def save(self, *args, **kwargs):
            raise DatabaseError('did not affect any rows')

    class TestObj(mixins.UpdatePreconditionsMixin, Base):
        pass

    obj = TestObj()
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        obj.save(pre_filters={'active': True})


def test_update_preconditions_save_reraises_unrelated() -> None:
    """Save re-raises DatabaseError that does not match 'did not affect'."""

    class Base:
        def save(self, *args, **kwargs):
            raise DatabaseError('connection lost')

    class TestObj(mixins.UpdatePreconditionsMixin, Base):
        pass

    obj = TestObj()
    with pytest.raises(DatabaseError, match='connection lost'):
        obj.save(pre_filters={'active': True})


def test_do_update_precondition_failure() -> None:
    """_do_update raises precondition error when row exists but update fails."""

    class Base:
        def _do_update(self, base_qs, using, pk, values, uf, fu):
            return False

    class TestObj(mixins.UpdatePreconditionsMixin, Base):
        pass

    obj = TestObj()
    obj._preconditions = ({}, {'active': True})
    base_qs = MagicMock()
    filtered_qs = MagicMock()
    base_qs.filter.return_value = filtered_qs
    filtered_qs.filter.return_value.exists.return_value = True

    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        obj._do_update(base_qs, 'default', 1, [], None, False)


# ---------------------------------------------------------------------------
# StateTransitionEventsMixin
# ---------------------------------------------------------------------------


def test_state_transition_events_init() -> None:
    """__init__ stores current state as previous_state."""

    class Base:
        def __init__(self):
            self.state = 'PENDING'

    class TestObj(mixins.StateTransitionEventsMixin, Base):
        pass

    obj = TestObj()
    assert obj.previous_state == 'PENDING'


def test_state_transition_events_fires_signal() -> None:
    """save() fires post_state_transition signal when state is updated."""

    class Base:
        def __init__(self):
            self.state = 'PENDING'

        def save(self, *args, **kwargs):
            pass

    class TestObj(mixins.StateTransitionEventsMixin, Base):
        pass

    obj = TestObj()
    obj.state = 'RUNNING'

    with patch.object(
        mixins.signals.post_state_transition,
        'send',
    ) as mock_send:
        obj.save(update_fields=['state'])
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs['instance'] is obj
        assert call_kwargs['previous_state'] == 'PENDING'


def test_state_transition_events_updates_previous() -> None:
    """After save with state update, previous_state is updated."""

    class Base:
        def __init__(self):
            self.state = 'PENDING'

        def save(self, *args, **kwargs):
            pass

    class TestObj(mixins.StateTransitionEventsMixin, Base):
        pass

    obj = TestObj()
    obj.state = 'RUNNING'

    with patch.object(
        mixins.signals.post_state_transition,
        'send',
    ):
        obj.save(update_fields=['state'])
    assert obj.previous_state == 'RUNNING'


def test_state_transition_events_no_signal_without_state() -> None:
    """save() does not fire signal when state is not in update_fields."""

    class Base:
        def __init__(self):
            self.state = 'PENDING'

        def save(self, *args, **kwargs):
            pass

    class TestObj(mixins.StateTransitionEventsMixin, Base):
        pass

    obj = TestObj()
    with patch.object(
        mixins.signals.post_state_transition,
        'send',
    ) as mock_send:
        obj.save(update_fields=['name'])
        mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# StateTransitionPreconditionMixin
# ---------------------------------------------------------------------------


def _make_state_machine(current_state='PENDING'):
    """Create a state-machine test object."""

    class States:
        TRANSITIONS = {
            'PENDING': {'RUNNING', 'CANCELLED'},
            'RUNNING': {'COMPLETED', 'FAILED'},
            'COMPLETED': set(),
            'CANCELLED': set(),
            'FAILED': set(),
        }

        @staticmethod
        def get_transit_from(state, auto_inverse=False):
            # Return states that can transition TO the given state
            sources = {s for s, targets in States.TRANSITIONS.items() if state in targets}
            return sources, True  # valid=True means use filter

    class Base:
        def save(self, *args, **kwargs):
            pass

        def _do_update(self, base_qs, using, pk, values, uf, fu):
            return True

    class TestObj(mixins.StateTransitionPreconditionMixin, Base):
        pass

    obj = TestObj()
    obj.state = current_state
    obj.states = States()
    return obj


def test_can_transit_to_allowed() -> None:
    """can_transit_to returns True for allowed transitions."""
    obj = _make_state_machine()
    assert obj.can_transit_to('RUNNING') is True


def test_can_transit_to_not_allowed() -> None:
    """can_transit_to returns False for disallowed transitions (fail=False)."""
    obj = _make_state_machine()
    assert obj.can_transit_to('COMPLETED') is False


def test_can_transit_to_raises_on_fail() -> None:
    """can_transit_to raises TransitionNotAllowedError when fail=True."""
    obj = _make_state_machine()
    with pytest.raises(exceptions.TransitionNotAllowedError):
        obj.can_transit_to('COMPLETED', fail=True)


def test_can_transit_to_noop_skip() -> None:
    """can_transit_to returns False for same state with noop_skip=True."""
    obj = _make_state_machine()
    assert obj.can_transit_to('PENDING', fail=True, noop_skip=True) is False


def test_check_state_in_valid() -> None:
    """check_state_in returns True when state is in the given set."""
    obj = _make_state_machine()
    assert obj.check_state_in(['PENDING', 'RUNNING']) is True


def test_check_state_in_invalid() -> None:
    """check_state_in returns False when state is not in the given set."""
    obj = _make_state_machine()
    assert obj.check_state_in(['COMPLETED']) is False


def test_check_state_in_raises_on_fail() -> None:
    """check_state_in raises InvalidStateError when fail=True."""
    obj = _make_state_machine()
    with pytest.raises(exceptions.InvalidStateError):
        obj.check_state_in(['COMPLETED'], fail=True)


def test_state_transition_pop_preconditions_adds_state_filter() -> None:
    """pop_preconditions auto-adds state filter when state is being saved."""
    obj = _make_state_machine(current_state='RUNNING')
    _args, _kwargs, has = obj.pop_preconditions(
        update_fields=['state'],
    )
    assert has is True
    pre_excludes, pre_filters = obj._preconditions
    # Should have a state filter from get_transit_from
    has_state = any(k.startswith('state') for k in {**pre_excludes, **pre_filters})
    assert has_state


# ---------------------------------------------------------------------------
# RelatedModelMixin
# ---------------------------------------------------------------------------


def test_related_model_mixin_delegates() -> None:
    """get_related_manager and get_related_model delegate to utils."""

    class TestObj(mixins.RelatedModelMixin):
        _meta = MagicMock()

    mock_model = MagicMock()
    TestObj._meta.get_field.return_value.related_model = mock_model
    mock_model._default_manager = MagicMock()

    result = TestObj.get_related_model('author')
    assert result is mock_model

    result = TestObj.get_related_manager('author')
    assert result is mock_model._default_manager
