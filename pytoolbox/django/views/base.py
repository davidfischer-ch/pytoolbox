"""
Extra views.
"""
from __future__ import annotations

from django.http import HttpResponseRedirect
from django.views.generic.edit import DeleteView

__all__ = ['CancellableDeleteView']


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)
