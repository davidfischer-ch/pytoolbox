from __future__ import annotations

from collections import OrderedDict
from unittest.mock import MagicMock

from django.forms import fields

from pytoolbox.django.forms import mixins


def test_enctype_mixin() -> None:
    class FakeForm(mixins.EnctypeMixin):
        def is_multipart(self):
            return False

    assert FakeForm().enctype == 'application/x-www-form-urlencoded'

    class FakeMultipartForm(mixins.EnctypeMixin):
        def is_multipart(self):
            return True

    assert FakeMultipartForm().enctype == 'multipart/form-data'


def test_map_errors_mixin() -> None:
    added_errors = {}

    class Base:
        def add_error(self, field, error):
            added_errors[field] = error

    class FakeForm(mixins.MapErrorsMixin, Base):
        errors_map = {'old_field': 'new_field'}

    form = FakeForm()
    form.add_error('old_field', 'some error')
    assert 'new_field' in added_errors
    assert 'old_field' not in added_errors


def test_request_mixin() -> None:
    form = mixins.RequestMixin()
    assert form.request is None
    form = mixins.RequestMixin(request='my_request')
    assert form.request == 'my_request'


def test_staff_only_fields_mixin_removes_for_non_staff() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            kwargs.pop('request', None)
            self.fields = OrderedDict([
                ('name', fields.CharField()),
                ('secret', fields.CharField()),
                ('public', fields.CharField())
            ])

    class FakeForm(mixins.StaffOnlyFieldsMixin, Base):
        staff_only_fields = ('secret',)

    request = MagicMock()
    request.user.is_staff = False
    form = FakeForm(request=request)
    assert 'secret' not in form.fields
    assert 'name' in form.fields
    assert 'public' in form.fields


def test_staff_only_fields_mixin_keeps_for_staff() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            kwargs.pop('request', None)
            self.fields = OrderedDict([
                ('name', fields.CharField()),
                ('secret', fields.CharField())
            ])

    class FakeForm(mixins.StaffOnlyFieldsMixin, Base):
        staff_only_fields = ('secret',)

    request = MagicMock()
    request.user.is_staff = True
    form = FakeForm(request=request)
    assert 'secret' in form.fields
    assert 'name' in form.fields


def test_created_by_mixin_sets_user() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            kwargs.pop('request', None)
            self.instance = MagicMock()
            self.instance.created_by_id = None

        def save(self, commit=True):
            return self.instance

    class FakeForm(mixins.CreatedByMixin, Base):
        pass

    request = MagicMock()
    form = FakeForm(request=request)
    form.save()
    assert form.instance.created_by is request.user


def test_created_by_mixin_skips_existing() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            kwargs.pop('request', None)
            self.instance = MagicMock()
            self.instance.created_by_id = 42

        def save(self, commit=True):
            return self.instance

    class FakeForm(mixins.CreatedByMixin, Base):
        pass

    request = MagicMock()
    form = FakeForm(request=request)
    form.save()
    # created_by should not be overwritten when created_by_id is already set
    assert form.instance.created_by_id == 42


def test_model_based_form_cleanup_mixin_delegates() -> None:
    class Base:
        def clean(self):
            pass

    class FakeForm(mixins.ModelBasedFormCleanupMixin, Base):
        class _meta:
            model = MagicMock()

        cleaned_data = {'field': 'value'}

    FakeForm._meta.model.clean_form.return_value = {'field': 'cleaned'}
    form = FakeForm()
    result = form.clean()
    FakeForm._meta.model.clean_form.assert_called_once_with(form)
    assert result == {'field': 'cleaned'}


def test_model_based_form_cleanup_mixin_fallback() -> None:
    class Base:
        def clean(self):
            pass

    class FakeForm(mixins.ModelBasedFormCleanupMixin, Base):
        class _meta:
            model = object()  # No clean_form method

        cleaned_data = {'field': 'value'}

    form = FakeForm()
    result = form.clean()
    assert result == {'field': 'value'}


def test_help_text_to_placeholder_mixin() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            self.fields = OrderedDict([
                ('name', fields.CharField(help_text='Enter name'))
            ])

    class FakeForm(mixins.HelpTextToPlaceholderMixin, Base):
        pass

    form = FakeForm()
    assert form.fields['name'].widget.attrs['placeholder'] == 'Enter name'
    assert form.fields['name'].help_text is None


def test_convert_email_to_text_mixin() -> None:
    class Base:
        def __init__(self, *args, **kwargs):
            self.fields = OrderedDict([
                ('email', fields.EmailField()),
                ('name', fields.CharField())
            ])

    class FakeForm(mixins.ConvertEmailToTextMixin, Base):
        pass

    form = FakeForm()
    assert form.fields['email'].widget.input_type == 'text'
    assert form.fields['name'].widget.input_type == 'text'  # CharField is also 'text'
