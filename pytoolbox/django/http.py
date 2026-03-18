"""Utilities for building Django HTTP responses."""
from __future__ import annotations

import urllib.parse

from django.http import HttpResponse


def set_attachment(request, response: HttpResponse, filename: str) -> None:  # pylint:disable=unused-argument
    """
    Set the ``Content-Disposition`` header on *response* to trigger a file download.

    Encodes *filename* per RFC 2231 (``filename*=UTF-8''<percent-encoded>``), which
    handles non-ASCII filenames across all modern browsers.
    """
    filename_quoted = urllib.parse.quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{filename_quoted}"
