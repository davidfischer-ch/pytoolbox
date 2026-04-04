"""
Extra storages and mix-ins for building your own storages.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import time

from django.core.files.storage import FileSystemStorage

from pytoolbox import logging, module

_all = module.All(globals())

logger = logging.get_logger(__name__)


class ExpressTemporaryFileMixin:
    """Speed up saving by enabling rename for temporary uploaded files."""

    def _save(self, name: str, content: object) -> str:
        """
        Save the temporary file to the storage.
        Set temporary file path to allow using rename instead of chunked copy when possible.

        See what happens in super()._save():
            https://github.com/django/django/blob/master/django/core/files/storage.py
        """
        start_time = time.time()
        if hasattr(content.file, 'temporary_file_path'):
            content.temporary_file_path = content.file.temporary_file_path
        result = super()._save(name, content)
        logger.debug('Saved protected file "%s" in %.2g seconds', name, time.time() - start_time)
        return result


class OverwriteMixin:
    """
    Update get_available_name to remove any previously stored file (if any) before returning the
    name.
    """

    def get_available_name(self, name: str) -> str:
        """Delete any existing file at *name* and return it as available."""
        self.delete(name)
        return name


class OverwriteFileSystemStorage(OverwriteMixin, FileSystemStorage):
    """A file-system based storage that let overwrite files with the same name."""


__all__ = _all.diff(globals())
