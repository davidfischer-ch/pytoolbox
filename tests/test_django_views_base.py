"""Tests for the django.views.base module."""

# pylint:disable=no-member,too-few-public-methods
from __future__ import annotations

from collections.abc import Iterator

import pytest
from django.db import connection, models
from django.test import RequestFactory

from pytoolbox.django.views import base


class Bookmark(models.Model):
    """A row the delete view removes."""

    name = models.CharField(max_length=50)

    class Meta:
        """Model metadata."""

        app_label = 'test'


class BookmarkDeleteView(base.CancellableDeleteView):
    """Delete view configured as Django documents it, with a success URL."""

    model = Bookmark
    success_url = '/bookmarks/'


@pytest.fixture(name='bookmark')
def fixture_bookmark() -> Iterator[Bookmark]:
    """Create the bookmarks table, and one bookmark in it, for one test."""
    with connection.schema_editor() as editor:
        editor.create_model(Bookmark)
    yield Bookmark.objects.create(name='docs')
    with connection.schema_editor() as editor:
        editor.delete_model(Bookmark)


# --- CancellableDeleteView ------------------------------------------------------------------------


def test_cancellable_delete_view_cancel_redirects_and_keeps_the_object(bookmark: Bookmark) -> None:
    """Cancelling redirects to the success URL and deletes nothing."""
    request = RequestFactory().post(f'/bookmarks/{bookmark.pk}/delete/', {'cancel': '1'})

    response = BookmarkDeleteView.as_view()(request, pk=bookmark.pk)

    assert (response.status_code, response.url) == (302, '/bookmarks/')
    assert Bookmark.objects.filter(pk=bookmark.pk).exists()
