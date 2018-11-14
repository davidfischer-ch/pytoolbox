# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own `Django Form Tools <https://github.com/django/django-formtools>`_
powered views.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module
from pytoolbox.django import forms

_all = module.All(globals())


class CrispyFormsMixin(object):

    def get_context_data(self, form, **kwargs):
        """Add the management form to the form for working with crispy forms."""
        from crispy_forms import layout
        context = super(CrispyFormsMixin, self).get_context_data(form=form, **kwargs)
        context['wizard']['form'].helper.layout.append(
            layout.HTML(context['wizard']['management_form']))
        context['form'] = context['wizard']['form']
        return context


class DataTableViewCompositionMixin(object):
    """Compose the wizard with some tables views."""

    table_view_classes = {}

    def get(self, request, *args, **kwargs):
        """Retrieve the table view and delegate AJAX to the table view."""
        if self.request.is_ajax():
            view = self.get_table_view()
            if view:
                return view.get_ajax(request, *args, **kwargs)
        return super(DataTableViewCompositionMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Update the context with the context returned by the table view."""
        context = super(DataTableViewCompositionMixin, self).get_context_data(**kwargs)
        view = self.get_table_view()
        if view:
            context.update(view.get_context_data())
        return context

    def get_table_view(self):
        """Return an instance of the datatable-view for current step, defaults to None."""
        view_class = self.table_view_classes.get(self.steps.current)
        if view_class:
            view = view_class()
            view.object_list = None
            view.request = self.request
            return view


class SerializeStepInstanceMixin(object):

    serialized_instance_form_class = forms.SerializedInstanceForm
    serialized_instances_key = 'serialized-instances'

    @property
    def serialized_instances(self):
        try:
            return self.storage.extra_data[self.serialized_instances_key]
        except KeyError:
            value = self.storage.extra_data[self.serialized_instances_key] = {}
            return value

    def serialize_step_instance(self, form, step=None):
        self.serialized_instances[step or self.steps.current] = \
            self.serialized_instance_form_class.serialize(form.save())

    # WizardView "Standard Methods"

    def get_form(self, step=None, *args, **kwargs):
        if step is None:
            step = self.steps.current
        if step in self.serialized_instances.iterkeys():
            self.form_list[step] = self.serialized_instance_form_class
        return super(SerializeStepInstanceMixin, self).get_form(step, *args, **kwargs)

    def get_form_kwargs(self, step):
        form_kwargs = super(SerializeStepInstanceMixin, self).get_form_kwargs(step)
        serialized_instance = self.serialized_instances.get(step, None)
        if serialized_instance:
            form_kwargs.update(serialized_instance)
        return form_kwargs


__all__ = _all.diff(globals())
