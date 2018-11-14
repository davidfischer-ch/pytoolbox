# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own forms.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.forms import fields

from pytoolbox import module

from . import utils, widgets

_all = module.All(globals())


class ConvertEmailToTextMixin(object):
    """
    Set email inputs as text to avoid the i18n issue
    http://html5doctor.com/html5-forms-input-types#input-email.
    """

    def __init__(self, *args, **kwargs):
        super(ConvertEmailToTextMixin, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            if getattr(field.widget, 'input_type', None) == 'email':
                field.widget.input_type = 'text'


class EnctypeMixin(object):

    @property
    def enctype(self):
        return 'multipart/form-data' if self.is_multipart() else 'application/x-www-form-urlencoded'


class HelpTextToPlaceholderMixin(object):
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
        fields.TimeField
    )
    #: Remove the help text after having copied it to the placeholder.
    placeholder_remove_help_text = True

    def __init__(self, *args, **kwargs):
        super(HelpTextToPlaceholderMixin, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            if field and isinstance(field, self.placeholder_fields):
                self.set_placeholder(name, field)

    def set_placeholder(self, name, field):  # pylint:disable=unused-argument
        field.widget.attrs['placeholder'] = field.help_text
        if self.placeholder_remove_help_text:
            field.help_text = None


class MapErrorsMixin(object):
    """
    Map errors based on field name. Mandatory when the form contains a field from a model named
    differently.
    """

    errors_map = {}

    def add_error(self, field, error):
        field = self.errors_map.get(field, field)
        return super(MapErrorsMixin, self).add_error(field, error)


class ModelBasedFormCleanupMixin(object):
    """
    Make possible the cleanup of the form by the model through a class method called `clean_form`.
    Useful to cleanup the form based on complex conditions, e.g. if two fields are inter-related
    (start/end dates, ...).
    """

    def clean(self):
        super(ModelBasedFormCleanupMixin, self).clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


class RequestMixin(object):
    """
    Accept request as a optional (default: None) argument of the constructor and set it as an
    attribute of the object.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(RequestMixin, self).__init__(*args, **kwargs)


class CreatedByMixin(RequestMixin):
    """Set instance's created_by field to current user if the instance is just created."""

    def save(self, commit=True):
        if hasattr(self.instance, 'created_by_id') and not self.instance.created_by_id:
            self.instance.created_by = self.request.user
        return super(CreatedByMixin, self).save(commit=commit)


class StaffOnlyFieldsMixin(RequestMixin):
    """Hide some fields if authenticated user is not a member of the staff."""

    staff_only_fields = ()

    def __init__(self, *args, **kwargs):
        super(StaffOnlyFieldsMixin, self).__init__(*args, **kwargs)
        if not self.request or not self.request.user.is_staff:
            for field in self.staff_only_fields:
                self.fields.pop(field, None)


class UpdateWidgetAttributeMixin(object):
    """
    Update the widgets of the form based on a set of rules applied depending of the form field's
    class. The rules can change the class of the widget and/or update the attributes of the widget
    with :func:`pytoolbox.django.forms.utils.update_widget_attributes`.
    """

    #: Set of rules linking the form field's class to the replacement class and the attributes
    #  update list.
    widgets_rules = {
        fields.DateField: [widgets.CalendarDateInput, {'class': '+dateinput +input-small'}],
        fields.TimeField: [widgets.ClockTimeInput,    {'class': '+timeinput +input-small'}],
    }
    #: Attributes that are applied to all widgets of the form
    widgets_common_attrs = {}

    def __init__(self, *args, **kwargs):
        super(UpdateWidgetAttributeMixin, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            updates = self.widgets_rules.get(field.__class__)
            # May Update widget class with rules-based replacement class
            if updates and updates[0]:
                field.widget = updates[0]()
            # May update widget attributes with common attributes
            if self.widgets_common_attrs:
                utils.update_widget_attributes(field.widget, self.widgets_common_attrs)
            # May update widget attributes with rules-based attributes
            if updates and updates[1]:
                utils.update_widget_attributes(field.widget, updates[1])
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass


__all__ = _all.diff(globals())
