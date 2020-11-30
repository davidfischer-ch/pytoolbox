"""
Extra storages and mix-ins for building your own storages.
"""

import logging, time

from django.core.files.storage import FileSystemStorage

from pytoolbox import module

_all = module.All(globals())

logger = logging.getLogger(__name__)


class ExpressTemporaryFileMixin(object):

    def _save(self, name, content):
        """
        Save the temporary file to the storage.
        Set temporary file path to allow using rename instead of chunked copy when possible.

        See what happens in super()._save():
            https://github.com/django/django/blob/master/django/core/files/storage.py
        """
        start_time = time.time()
        if hasattr(content.file, 'temporary_file_path'):
            content.temporary_file_path = lambda: content.file.temporary_file_path()
        result = super()._save(name, content)
        logger.debug(f'Saved protected file "{name}" in {time.time() - start_time:.2g} seconds')
        return result


class OverwriteMixin(object):
    """
    Update get_available_name to remove any previously stored file (if any) before returning the
    name.
    """

    def get_available_name(self, name):
        self.delete(name)
        return name


class OverwriteFileSystemStorage(OverwriteMixin, FileSystemStorage):
    """A file-system based storage that let overwrite files with the same name."""


__all__ = _all.diff(globals())
