from __future__ import annotations

from unittest.mock import MagicMock

from django.db import models

from pytoolbox.django.models import mixins


def test_faster_validate_on_save_mixin_uses_is_relation() -> None:
    """Relation fields are excluded from validation, regular fields are not."""
    class TestModel(mixins.FasterValidateOnSaveMixin, models.Model):
        name = models.CharField(max_length=100)
        other = models.ForeignKey(
            'auth.User',
            on_delete=models.CASCADE,
            null=True)

        class Meta:
            app_label = 'test'

    instance = TestModel.__new__(TestModel)
    kwargs = instance.validate_on_save_kwargs
    assert 'other' in kwargs['exclude']
    assert 'name' not in kwargs['exclude']


def test_public_meta_mixin() -> None:
    """meta() classmethod exposes the private _meta for use in templates."""
    class TestModel(mixins.PublicMetaMixin, models.Model):
        class Meta:
            app_label = 'test'

    assert TestModel.meta() is TestModel._meta  # pylint:disable=no-member


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
    """save(validate=False) bypasses full_clean() even when validate_on_save is True."""
    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class TestObj(mixins.ValidateOnSaveMixin, Base):
        full_clean = MagicMock()

    obj = TestObj()
    obj.save(validate=False)
    obj.full_clean.assert_not_called()


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
    """Without update_fields, always_update_fields does not force a partial update."""
    saved_kwargs = {}

    class Base:
        def save(self, *args, **kwargs):  # pylint:disable=unused-argument
            saved_kwargs.update(kwargs)

    class TestObj(mixins.AlwaysUpdateFieldsMixin, Base):
        always_update_fields = ('modified_at',)

    obj = TestObj()
    obj.save()
    assert 'update_fields' not in saved_kwargs


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
