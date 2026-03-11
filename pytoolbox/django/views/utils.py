"""
Some utilities related to the view layer.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404

if TYPE_CHECKING:
    from django.db import models as db_models

__all__ = ['get_model_or_404']


def get_model_or_404(name: str, *models: type[db_models.Model]) -> type[db_models.Model]:
    """
    Return the model whose ``model_name`` matches *name*,
    or raise :class:`~django.http.Http404`.
    """
    try:
        return next(m for m in models if m._meta.model_name == name)
    except StopIteration as ex:
        raise Http404() from ex
