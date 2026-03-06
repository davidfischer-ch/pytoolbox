from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytoolbox.rest_framework.serializers import mixins


def test_read_only_mixin_sets_read_only() -> None:
    """ReadOnlyMixin forces read_only=True on the serializer."""
    class Base:
        def __init__(self, *args, **kwargs):  # pylint:disable=unused-argument
            self.read_only = kwargs.get('read_only')

    class FakeSerializer(mixins.ReadOnlyMixin, Base):
        pass

    serializer = FakeSerializer()
    assert serializer.read_only is True


def test_read_only_mixin_create_raises() -> None:
    """create() raises AttributeError to enforce read-only behavior."""
    class Base:
        def __init__(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class FakeSerializer(mixins.ReadOnlyMixin, Base):
        pass

    serializer = FakeSerializer()
    with pytest.raises(AttributeError, match='Read-only'):
        serializer.create({})


def test_read_only_mixin_update_raises() -> None:
    """update() raises AttributeError to enforce read-only behavior."""
    class Base:
        def __init__(self, *args, **kwargs):  # pylint:disable=unused-argument
            pass

    class FakeSerializer(mixins.ReadOnlyMixin, Base):
        pass

    serializer = FakeSerializer()
    with pytest.raises(AttributeError, match='Read-only'):
        serializer.update(None, {})


def test_nested_write_mixin_returns_tuple() -> None:
    """to_internal_value returns (serializer, validated_data) for nested write support."""
    class Base:
        def to_internal_value(self, data):
            return {'key': data}

    class FakeSerializer(mixins.NestedWriteMixin, Base):
        pass

    serializer = FakeSerializer()
    result = serializer.to_internal_value('test')
    assert isinstance(result, tuple)
    assert result[0] is serializer
    assert result[1] == {'key': 'test'}


def test_from_private_key_mixin_dict_delegates_to_super() -> None:
    """Dict input is passed through to the parent serializer for normal deserialization."""
    class Base:
        def to_internal_value(self, data):
            return data

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        pass

    serializer = FakeSerializer()
    assert serializer.to_internal_value({'name': 'test'}) == {'name': 'test'}


def test_from_private_key_mixin_empty_delegates_to_super() -> None:
    """Empty or None input is passed through to the parent serializer."""
    class Base:
        def to_internal_value(self, data):
            return data

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        pass

    serializer = FakeSerializer()
    assert serializer.to_internal_value({}) == {}
    assert serializer.to_internal_value(None) is None


def test_from_private_key_mixin_pk_lookup() -> None:
    """Scalar input triggers a pk lookup on the model instead of deserialization."""
    mock_instance = MagicMock()

    class Base:
        def to_internal_value(self, data):
            return data

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        class Meta:
            model = MagicMock()

    FakeSerializer.Meta.model.objects.get.return_value = mock_instance
    serializer = FakeSerializer()
    result = serializer.to_internal_value(42)
    FakeSerializer.Meta.model.objects.get.assert_called_once_with(pk=42)
    assert result is mock_instance


def test_from_private_key_mixin_create_returns_instance() -> None:
    """create() returns the instance directly when validated_data is already a model instance."""
    class FakeModel:
        pass

    instance = FakeModel()

    class Base:
        def create(self, validated_data):  # pylint:disable=unused-argument
            return 'created'

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        class Meta:
            model = FakeModel

    serializer = FakeSerializer()
    assert serializer.create(instance) is instance


def test_from_private_key_mixin_create_delegates_for_dict() -> None:
    """create() delegates to super when validated_data is a dict."""
    class Base:
        def create(self, validated_data):  # pylint:disable=unused-argument
            return 'created'

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        class Meta:
            model = MagicMock

    serializer = FakeSerializer()
    assert serializer.create({'name': 'test'}) == 'created'


def test_from_private_key_mixin_does_not_exist() -> None:
    """ObjectDoesNotExist triggers self.fail('does_not_exist')."""
    from django.core.exceptions import ObjectDoesNotExist

    class Base:
        def to_internal_value(self, data):
            return data

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        class Meta:
            model = MagicMock()

        def fail(self, key, **kwargs):
            raise AssertionError(f'fail called with {key}')

    FakeSerializer.Meta.model.objects.get.side_effect = ObjectDoesNotExist()
    serializer = FakeSerializer()
    with pytest.raises(AssertionError, match='does_not_exist'):
        serializer.to_internal_value(999)


def test_from_private_key_mixin_incorrect_type() -> None:
    """TypeError/ValueError triggers self.fail('incorrect_type')."""
    class Base:
        def to_internal_value(self, data):
            return data

    class FakeSerializer(mixins.FromPrivateKeyMixin, Base):
        class Meta:
            model = MagicMock()

        def fail(self, key, **kwargs):
            raise AssertionError(f'fail called with {key}')

    FakeSerializer.Meta.model.objects.get.side_effect = TypeError('bad type')
    serializer = FakeSerializer()
    with pytest.raises(AssertionError, match='incorrect_type'):
        serializer.to_internal_value(object())
