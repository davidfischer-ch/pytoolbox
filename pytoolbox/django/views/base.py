"""
Extra views.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.views.generic.edit import DeleteView

__all__ = ['CancellableDeleteView']


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        """Redirect to :attr:`success_url` if cancel is in POST data."""
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)
