"""
Some utilities related to the view layer.
"""
from __future__ import annotations

from django.http import Http404

__all__ = ['get_model_or_404']


def get_model_or_404(name, *models):
    try:
        return next(m for m in models if m._meta.model_name == name)
    except StopIteration:
        raise Http404()
