from __future__ import annotations

from unittest.mock import MagicMock

from django.http import Http404
import pytest

from pytoolbox.django.views import utils


def test_get_model_or_404() -> None:
    """Returns the model matching model_name, raises Http404 for unknown names."""
    model_a = MagicMock()
    model_a._meta.model_name = 'article'
    model_b = MagicMock()
    model_b._meta.model_name = 'comment'

    assert utils.get_model_or_404('article', model_a, model_b) is model_a
    assert utils.get_model_or_404('comment', model_a, model_b) is model_b
    with pytest.raises(Http404):
        utils.get_model_or_404('missing', model_a, model_b)
