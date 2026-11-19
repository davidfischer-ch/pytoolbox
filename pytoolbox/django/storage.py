"""
Extra storages and mix-ins for building your own storages.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from django.core.files import File
from django.core.files.storage import FileSystemStorage

from pytoolbox import logging, module

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


class OverwriteFileSystemStorage(FileSystemStorage):
    """
    File-system storage replacing the file stored under the name of a file saved.

    .. deprecated:: 14.13.0
       Use ``FileSystemStorage(allow_overwrite=True)`` instead.
    """

    def __init__(self, *args: Any, allow_overwrite: bool = True, **kwargs: Any) -> None:
        warnings.warn(
            'OverwriteFileSystemStorage is deprecated; '
            'use django.core.files.storage.FileSystemStorage(allow_overwrite=True).',
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, allow_overwrite=allow_overwrite, **kwargs)

    @override
    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        """
        Return the base storage's available name, the file or symbolic link stored under it deleted.

        Deleting it, a link included, makes the save create a new file instead of writing through.
        """
        name = super().get_available_name(name, max_length=max_length)
        Path(self.path(name)).unlink(missing_ok=True)
        return name


class OverwriteMixin(_StorageMixin):
    """
    Mix-in deleting the file stored under a name before returning the name as available.

    .. deprecated:: 14.13.0
       Use ``FileSystemStorage(allow_overwrite=True)`` instead, or django-storages'
       ``file_overwrite``.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            'OverwriteMixin is deprecated; use '
            'django.core.files.storage.FileSystemStorage(allow_overwrite=True), '
            "or django-storages' file_overwrite.",
            DeprecationWarning,
            stacklevel=2,
        )

    @override
    def get_alternative_name(self, file_root: str, file_ext: str) -> str:
        """Return the name itself, to be cut by the base storage until it fits."""
        return f'{file_root}{file_ext}'

    @override
    def get_available_name(self, name: str, max_length: int | None = None) -> str:
        """Return *name*, cut to *max_length* with its extension kept, its stored file deleted."""
        name = super().get_available_name(name, max_length=max_length)
        self.delete(name)
        return name

    @override
    def is_name_available(self, name: str, max_length: int | None = None) -> bool:
        """Return whether *name* fits *max_length*, a stored file being replaced."""
        return not (max_length and len(name) > max_length)


__all__ = _all.diff(globals())
