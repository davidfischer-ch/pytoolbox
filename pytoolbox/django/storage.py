"""
Extra storages and mix-ins for building your own storages.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from django.core.files import File
from django.core.files.storage import FileSystemStorage

from pytoolbox import logging, module
from pytoolbox.compat import override

# Both mixins complete a Storage and call into it; naming the base under TYPE_CHECKING states that
# requirement for the checker only.
_StorageMixin = FileSystemStorage if TYPE_CHECKING else object

_all = module.All(globals())

logger = logging.get_logger(__name__)


class ExpressTemporaryFileMixin(_StorageMixin):
    """Speed up saving by enabling rename for temporary uploaded files."""

    def _save(self, name: str, content: File) -> str:  # pyrefly: ignore[missing-attribute]
        """
        Save the temporary file to the storage.
        Set temporary file path to allow using rename instead of chunked copy when possible.

        See what happens in super()._save():
            https://github.com/django/django/blob/master/django/core/files/storage.py
        """
        start_time = time.time()
        if hasattr(content.file, 'temporary_file_path'):
            # Django's own storage looks this attribute up on the content it is given.
            content.temporary_file_path = content.file.temporary_file_path  # type: ignore[attr-defined]
        result = super()._save(name, content)  # pyrefly: ignore[missing-attribute]
        logger.debug('Saved protected file "%s" in %.2g seconds', name, time.time() - start_time)
        return result


class OverwriteMixin(_StorageMixin):
    """
    Update get_available_name to remove any previously stored file (if any) before returning the
    name.
    """

    @override
    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        """Delete any existing file at *name* and return it as available."""
        self.delete(name)
        return name


class OverwriteFileSystemStorage(OverwriteMixin, FileSystemStorage):
    """A file-system based storage that let overwrite files with the same name."""


__all__ = _all.diff(globals())
