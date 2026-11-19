"""
Mix-ins for building your own
`Django Datatable View <https://github.com/pivotal-energy-solutions/django-datatable-view>`_
powered views.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, ClassVar, override

if TYPE_CHECKING:
    from datatableview.datatables import Datatable
    from datatableview.views import DatatableView
    from django.db.models import QuerySet

# The mixin completes a DatatableView and reads its attributes; naming the base under TYPE_CHECKING
# states that requirement for the checker only. django-datatable-view ships no type information:
# the checker reads the base as unknown and reports each @override below as a bad-override,
# ignored at its site.
_DatatableMixin = DatatableView if TYPE_CHECKING else object

__all__ = ['MultiTablesMixin']


class MultiTablesMixin(_DatatableMixin):
    """
    Mix-in serving several datatables from one :class:`datatableview.views.DatatableView`.

    .. deprecated:: 14.13.0
       Use :class:`datatableview.views.MultipleDatatableMixin` instead.
    """

    multi_default = 'default'
    multi_datatables: ClassVar[tuple[tuple[str, str], ...]] = ()
    request_name_key = 'datatable-name'

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            'MultiTablesMixin is deprecated; use datatableview.views.MultipleDatatableMixin.',
            DeprecationWarning,
            stacklevel=2,
        )

    def get_ajax_url(self, name: str | None = None) -> str:
        """Return the AJAX URL for the given datatable name."""
        return self.request.path + f'?{self.request_name_key}={self.get_datatable_name(name)}'

    @override
    # pyrefly: ignore[bad-override]
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return context data with all datatables grouped by name and label."""
        context = super().get_context_data(**kwargs)
        del context[self.get_datatable_context_name()]
        context['datatables'] = [
            (name, label, self.get_datatable(name)) for name, label in self.multi_datatables
        ]
        return context

    @override
    # pyrefly: ignore[bad-override]
    def get_datatable(self, name: str | None = None, **kwargs: Any) -> Datatable:
        """
        Return the datatable of the given name, by default the one the request names.

        Keep it as the view's datatable, the one an AJAX request is answered with.
        """
        name = self.get_datatable_name(name)
        datatables = self.__dict__.setdefault('_datatables_by_name', {})
        if name not in datatables:
            self.__dict__.pop('_datatable', None)
            datatables[name] = super().get_datatable(datatable_name=name, **kwargs)
        self._datatable = datatables[name]
        return self._datatable

    @override
    # pyrefly: ignore[bad-override]
    def get_datatable_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        """Return the datatable's arguments, with the queryset and AJAX URL of its name."""
        name = kwargs.pop('datatable_name')
        queryset = self.get_queryset(name)
        return super().get_datatable_kwargs(**kwargs) | {
            'model': self.model or queryset.model,
            'object_list': queryset,
            'url': self.get_ajax_url(name),
        }

    def get_datatable_name(self, name: str | None) -> str:
        """Return the datatable name from argument, request, or default."""
        return name or self.request.GET.get(self.request_name_key) or self.multi_default

    @override
    # pyrefly: ignore[bad-override]
    def get_queryset(self, name: str | None = None) -> QuerySet:
        """Return the queryset of the given datatable name, an empty one for an unknown name."""
        queryset = super().get_queryset()
        name = self.get_datatable_name(name)
        if name not in dict(self.multi_datatables):
            return queryset.none()
        return getattr(self, f'get_{name}_queryset')(queryset)
