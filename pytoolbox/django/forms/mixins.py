"""
Mix-ins for building your own forms.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.forms import fields

from pytoolbox import module
from pytoolbox.compat import override

from . import utils, widgets

if TYPE_CHECKING:
    from django import forms
    from django.db import models

# Each mixin below completes a Django form and reads its attributes (`fields`, `instance`,
# `cleaned_data`, ...); naming the base under TYPE_CHECKING states that for the checker only.
_FormsMixin = forms.BaseModelForm if TYPE_CHECKING else object

_all = module.All(globals())


class ConvertEmailToTextMixin(_FormsMixin):
    """
    Set email inputs as text to avoid the i18n issue
    http://html5doctor.com/html5-forms-input-types#input-email.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if getattr(field.widget, 'input_type', None) == 'email':
                field.widget.input_type = 'text'


class EnctypeMixin(_FormsMixin):
    """Provide an :attr:`enctype` property for use in form templates."""

    @property
    def enctype(self) -> str:
        """Return the appropriate HTML form ``enctype`` attribute value."""
        return 'multipart/form-data' if self.is_multipart() else 'application/x-www-form-urlencoded'


class HelpTextToPlaceholderMixin(_FormsMixin):
    """
    Update the widgets of the form to copy (and remove) the field's help text to the widget's
    placeholder.
    """

    #: Add a placeholder to the type of fields listed here.
    placeholder_fields = (
        fields.CharField,
        fields.DateField,
        fields.DateTimeField,
        fields.DecimalField,
        fields.EmailField,
        fields.FloatField,
        fields.IntegerField,
        fields.RegexField,
        fields.SlugField,
        fields.TimeField,
    )
    #: Remove the help text after having copied it to the placeholder.
    placeholder_remove_help_text = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field and isinstance(field, self.placeholder_fields):
                self.set_placeholder(name, field)

    def set_placeholder(  # pylint:disable=unused-argument
        self,
        name: str,
        field: fields.Field,
    ) -> None:
        """Copy the field's help text into the widget placeholder attribute."""
        field.widget.attrs['placeholder'] = field.help_text
        if self.placeholder_remove_help_text:
            # Django types help_text as a string, but clearing it outright is the point here.
            field.help_text = None  # pyrefly: ignore[bad-assignment]


class MapErrorsMixin(_FormsMixin):
    """
    Map errors based on field name. Mandatory when the form contains a field from a model named
    differently.
    """

    errors_map: ClassVar[dict[str | None, str | None]] = {}

    @override
    def add_error(self, field: str | None, error: Any) -> None:
        """Remap the field name through :attr:`errors_map` before adding."""
        field = self.errors_map.get(field, field)
        return super().add_error(field, error)


class ModelBasedFormCleanupMixin(_FormsMixin):
    """
    Make possible the cleanup of the form by the model through a class method called `clean_form`.
    Useful to cleanup the form based on complex conditions, e.g. if two fields are inter-related
    (start/end dates, ...).
    """

    @override
    def clean(self) -> dict[str, object]:
        """Delegate additional cleanup to the model's ``clean_form`` method."""
        super().clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


class RequestMixin(_FormsMixin):
    """
    Accept request as a optional (default: None) argument of the constructor and set it as an
    attribute of the object.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)


class CreatedByMixin(RequestMixin):
    """Set instance's created_by field to current user if the instance is just created."""

    @override
    def save(self, commit: bool = True) -> models.Model:
        """Set ``created_by`` to the current user on first save."""
        if hasattr(self.instance, 'created_by_id') and not self.instance.created_by_id:
            self.instance.created_by = self.request.user
        return super().save(commit=commit)


class StaffOnlyFieldsMixin(RequestMixin):
    """Hide some fields if authenticated user is not a member of the staff."""

    staff_only_fields = ()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not self.request or not self.request.user.is_staff:
            for field in self.staff_only_fields:
                self.fields.pop(field, None)


class UpdateWidgetAttributeMixin(_FormsMixin):
    """
    Update the widgets of the form based on a set of rules applied depending of the form field's
    class. The rules can change the class of the widget and/or update the attributes of the widget
    with :func:`pytoolbox.django.forms.utils.update_widget_attributes`.
    """

    #: Set of rules linking the form field's class to the replacement class and the attributes
    #  update list.
    widgets_rules: ClassVar[dict[type[fields.Field], list[Any]]] = {
        fields.DateField: [widgets.CalendarDateInput, {'class': '+dateinput +input-small'}],
        fields.TimeField: [widgets.ClockTimeInput, {'class': '+timeinput +input-small'}],
    }
    #: Attributes that are applied to all widgets of the form
    widgets_common_attrs: ClassVar[dict[str, Any]] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            updates = self.widgets_rules.get(type(field))
            # May Update widget class with rules-based replacement class
            if updates and updates[0]:
                widget_class = updates[0]
                assert isinstance(widget_class, type)  # noqa: S101
                field.widget = widget_class()
            # May update widget attributes with common attributes
            if self.widgets_common_attrs:
                utils.update_widget_attributes(field.widget, self.widgets_common_attrs)
            # May update widget attributes with rules-based attributes
            if updates and updates[1]:
                attrs = updates[1]
                assert isinstance(attrs, dict)  # noqa: S101
                utils.update_widget_attributes(field.widget, attrs)
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass


__all__ = _all.diff(globals())
