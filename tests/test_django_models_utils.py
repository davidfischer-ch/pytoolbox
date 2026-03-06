from __future__ import annotations

from unittest.mock import MagicMock

from pytoolbox.django.models import utils


def test_get_base_model_with_proxy() -> None:
    """Returns proxy_for_model when the model is a proxy."""
    cls = MagicMock()
    cls._meta.proxy_for_model = MagicMock()
    result = utils.get_base_model(cls)
    assert result is cls._meta.proxy_for_model


def test_get_base_model_without_proxy() -> None:
    """Returns _meta.model when proxy_for_model is falsy."""
    cls = MagicMock()
    cls._meta.proxy_for_model = None
    result = utils.get_base_model(cls)
    assert result is cls._meta.model


def test_get_related_model() -> None:
    """Returns the related model class for a given field name."""
    cls = MagicMock()
    expected = MagicMock()
    cls._meta.get_field.return_value.related_model = expected
    result = utils.get_related_model(cls, 'author')
    cls._meta.get_field.assert_called_once_with('author')
    assert result is expected


def test_get_related_model_pk_field() -> None:
    """Passing 'pk' resolves the PK attname before looking up the field."""
    cls = MagicMock()
    cls._meta.pk.attname = 'user_id'
    expected = MagicMock()
    cls._meta.get_field.return_value.related_model = expected
    result = utils.get_related_model(cls, 'pk')
    cls._meta.get_field.assert_called_once_with('user')
    assert result is expected


def test_get_related_manager() -> None:
    """Returns the default manager of the related model."""
    cls = MagicMock()
    related_model = MagicMock()
    cls._meta.get_field.return_value.related_model = related_model
    result = utils.get_related_manager(cls, 'author')
    assert result is related_model._default_manager


def test_try_get_field_success() -> None:
    """Returns the field value when the attribute exists."""
    instance = MagicMock()
    instance.name = 'Alice'
    result = utils.try_get_field(instance, 'name')
    assert result == 'Alice'


def test_try_get_field_related_does_not_exist() -> None:
    """Returns None when RelatedObjectDoesNotExist is raised."""
    class RelatedObjectDoesNotExist(Exception):
        pass

    instance = MagicMock()
    instance.__class__.__name__ = 'MyModel'
    type(instance).profile = property(
        lambda self: (_ for _ in ()).throw(
            RelatedObjectDoesNotExist('no profile')))
    # Simulate by using a side_effect on getattr
    instance_obj = MagicMock()

    def raise_related(*args):
        raise RelatedObjectDoesNotExist('no related')

    instance_obj.configure_mock(**{'profile': property(raise_related)})

    # Direct test with a real class
    class Holder:
        @property
        def profile(self):
            raise RelatedObjectDoesNotExist('missing')

    result = utils.try_get_field(Holder(), 'profile')
    assert result is None


def test_try_get_field_other_exception_reraises() -> None:
    """Non-RelatedObjectDoesNotExist exceptions are re-raised."""
    class Holder:
        @property
        def profile(self):
            raise ValueError('bad value')

    import pytest
    with pytest.raises(ValueError, match='bad value'):
        utils.try_get_field(Holder(), 'profile')
