"""Tests for the django.http module."""

from __future__ import annotations

from unittest import mock

from django.http import HttpResponse

from pytoolbox.django import http


def test_set_attachment_ascii():
    """set_attachment() sets Content-Disposition for ASCII filenames."""
    response = HttpResponse()
    http.set_attachment(mock.MagicMock(), response, 'archive.zip')
    assert response['Content-Disposition'] == "attachment; filename*=UTF-8''archive.zip"


def test_set_attachment_unicode():
    """set_attachment() sets Content-Disposition with UTF-8 encoding for unicode filenames."""
    response = HttpResponse()
    http.set_attachment(mock.MagicMock(), response, 'Ñoño.zip')
    assert response['Content-Disposition'] == "attachment; filename*=UTF-8''%C3%91o%C3%B1o.zip"
