"""
Extra views.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.views.generic.edit import DeleteView

from pytoolbox.compat import override

__all__ = ['CancellableDeleteView']


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    @override
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Redirect to :attr:`success_url` if cancel is in POST data."""
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.get_success_url())
        return super().post(request, *args, **kwargs)
