"""
Mix-ins for building your own
`Django Datatable View <https://github.com/pivotal-energy-solutions/django-datatable-view>`_
powered views.
"""
from __future__ import annotations

__all__ = ['MultiTablesMixin']


class MultiTablesMixin(object):
    """Implements the base code for using multiple django-datatable-views powered tables."""

    multi_default = 'default'
    multi_datatables = ()
    request_name_key = 'datatable-name'

    def get_ajax_url(self, name=None):
        return self.request.path + f'?{self.request_name_key}={self.get_datatable_name(name)}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        default_table = context.pop('datatable')
        context['datatables'] = [
            (
                name,
                label,
                (default_table if name == self.multi_default else self.get_datatable(name=name)))
            for name, label in self.multi_datatables
        ]
        return context

    def get_datatable(self, name=None):
        return self.get_datatable_structure(name=name)

    def get_datatable_name(self, name):
        return name or self.request.GET.get(self.request_name_key) or self.multi_default

    def get_datatable_structure(self, name=None):
        options = self._get_datatable_options()
        return self.datatable_structure_class(
            self.get_ajax_url(name=name),
            options,
            model=self.get_model())

    def get_queryset(self, name=None):
        qs = super().get_queryset()
        name = self.get_datatable_name(name)
        if name not in set(n for n, l in self.multi_datatables):
            return qs.none()  # Bad name, returns nothing!
        return getattr(self, f'get_{name}_queryset')(qs)
