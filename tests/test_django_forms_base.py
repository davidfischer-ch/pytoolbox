from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytoolbox.django.forms import base


def test_serialized_instance_form_init() -> None:
    """Stores app_label, model, and pk from kwargs."""
    form = base.SerializedInstanceForm(
        app_label='myapp',
        model='article',
        pk=42)
    assert form.app_label == 'myapp'
    assert form.model == 'article'
    assert form.pk == 42


def test_serialized_instance_form_serialize() -> None:
    """serialize() delegates to get_content_type_dict."""
    instance = MagicMock()
    expected = {'app_label': 'myapp', 'model': 'article', 'pk': 1}
    with patch(
        'pytoolbox.django.forms.base.utils.get_content_type_dict',
        return_value=expected
    ) as mock_ct:
        result = base.SerializedInstanceForm.serialize(instance)
        mock_ct.assert_called_once_with(instance)
        assert result == expected


def test_serialized_instance_form_instance_property() -> None:
    """Instance property calls get_instance and caches the result."""
    form = base.SerializedInstanceForm(
        app_label='myapp',
        model='article',
        pk=42)
    expected = MagicMock()
    with patch(
        'pytoolbox.django.forms.base.utils.get_instance',
        return_value=expected
    ) as mock_get:
        result = form.instance
        mock_get.assert_called_once_with('myapp', 'article', 42)
        assert result is expected


def test_serialized_instance_form_is_valid_true() -> None:
    """is_valid() returns True when instance exists."""
    form = base.SerializedInstanceForm(
        app_label='myapp',
        model='article',
        pk=42)
    with patch(
        'pytoolbox.django.forms.base.utils.get_instance',
        return_value=MagicMock()
    ):
        assert form.is_valid() is True


def test_serialized_instance_form_is_valid_false() -> None:
    """is_valid() returns False when get_instance raises an exception."""
    form = base.SerializedInstanceForm(
        app_label='myapp',
        model='article',
        pk=999)
    with patch(
        'pytoolbox.django.forms.base.utils.get_instance',
        side_effect=Exception('not found')
    ):
        assert form.is_valid() is False
