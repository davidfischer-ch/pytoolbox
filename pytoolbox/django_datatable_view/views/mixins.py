"""
Mix-ins for building your own
`Django Datatable View <https://github.com/pivotal-energy-solutions/django-datatable-view>`_
powered views.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models import QuerySet

__all__ = ['MultiTablesMixin']


class MultiTablesMixin(object):
    """Implements the base code for using multiple django-datatable-views powered tables."""

    multi_default = 'default'
    multi_datatables = ()
    request_name_key = 'datatable-name'

    def get_ajax_url(self, name: str | None = None) -> str:
        """Return the AJAX URL for the given datatable name."""
        return self.request.path + f'?{self.request_name_key}={self.get_datatable_name(name)}'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return context data with all datatables grouped by name and label."""
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

    def get_datatable(self, name: str | None = None) -> Any:
        """Return the datatable structure for the given name."""
        return self.get_datatable_structure(name=name)

    def get_datatable_name(self, name: str | None) -> str:
        """Return the datatable name from argument, request, or default."""
        return name or self.request.GET.get(self.request_name_key) or self.multi_default

    def get_datatable_structure(self, name: str | None = None) -> Any:
        """Return the datatable structure instance for the given name."""
        options = self._get_datatable_options()
        return self.datatable_structure_class(
            self.get_ajax_url(name=name),
            options,
            model=self.get_model())

    def get_queryset(self, name: str | None = None) -> QuerySet:
        """Return the queryset for the given datatable name."""
        qs = super().get_queryset()
        name = self.get_datatable_name(name)
        if name not in set(n for n, _ in self.multi_datatables):
            return qs.none()  # Bad name, returns nothing!
        return getattr(self, f'get_{name}_queryset')(qs)
