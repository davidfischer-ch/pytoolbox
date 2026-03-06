"""
Mix-ins for building your own `Django Form Tools <https://github.com/django/django-formtools>`_
powered views.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.forms import Form
    from django.http import HttpRequest, HttpResponse

from pytoolbox.django import forms

__all__ = ['CrispyFormsMixin', 'DataTableViewCompositionMixin', 'SerializeStepInstanceMixin']


class CrispyFormsMixin(object):
    """Integrate crispy-forms layout with the form wizard management form."""

    def get_context_data(self, form: Form, **kwargs: Any) -> dict[str, Any]:
        """Add the management form to the form for working with crispy forms."""
        from crispy_forms import layout
        context = super().get_context_data(form=form, **kwargs)
        context['wizard']['form'].helper.layout.append(
            layout.HTML(context['wizard']['management_form']))
        context['form'] = context['wizard']['form']
        return context


class DataTableViewCompositionMixin(object):
    """Compose the wizard with some tables views."""

    table_view_classes = {}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Retrieve the table view and delegate AJAX to the table view."""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            view = self.get_table_view()
            if view:
                return view.get_ajax(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Update the context with the context returned by the table view."""
        context = super().get_context_data(**kwargs)
        view = self.get_table_view()
        if view:
            context.update(view.get_context_data())
        return context

    def get_table_view(self) -> Any | None:
        """Return an instance of the datatable-view for current step, defaults to None."""
        view_class = self.table_view_classes.get(self.steps.current)
        if view_class:
            view = view_class()
            view.object_list = None
            view.request = self.request
            return view


class SerializeStepInstanceMixin(object):
    """Serialize and restore model instances across wizard steps."""

    serialized_instance_form_class = forms.SerializedInstanceForm
    serialized_instances_key = 'serialized-instances'

    @property
    def serialized_instances(self) -> dict[str, Any]:
        """Return the dictionary of serialized instances from storage."""
        try:
            return self.storage.extra_data[self.serialized_instances_key]
        except KeyError:
            value = self.storage.extra_data[self.serialized_instances_key] = {}
            return value

    def serialize_step_instance(self, form: Form, step: str | None = None) -> None:
        """Serialize the form's saved instance for the given step."""
        self.serialized_instances[step or self.steps.current] = \
            self.serialized_instance_form_class.serialize(form.save())

    # WizardView "Standard Methods"

    def get_form(self, step: str | None = None, *args: Any, **kwargs: Any) -> Form:
        """Return the form for the step, using serialized data if available."""
        if step is None:
            step = self.steps.current
        if step in self.serialized_instances.keys():
            self.form_list[step] = self.serialized_instance_form_class
        return super().get_form(step, *args, **kwargs)

    def get_form_kwargs(self, step: str) -> dict[str, Any]:
        """Return form kwargs, merging in serialized instance data if present."""
        form_kwargs = super().get_form_kwargs(step)
        serialized_instance = self.serialized_instances.get(step, None)
        if serialized_instance:
            form_kwargs.update(serialized_instance)
        return form_kwargs
