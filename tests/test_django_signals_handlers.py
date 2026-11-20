"""Tests for the django.signals.handlers module."""

# pylint:disable=no-member,too-few-public-methods
from __future__ import annotations

from typing import override

from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.db import models

from pytoolbox.django.signals import handlers


class RemoteStorage(Storage):  # pylint:disable=abstract-method
    """A storage keeping the files in memory, without local paths, as a cloud storage does."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    @override
    def _save(self, name: str, content: File) -> str:
        self.files[name] = content.read()
        return name

    @override
    def delete(self, name: str) -> None:
        del self.files[name]

    @override
    def exists(self, name: str) -> bool:
        return name in self.files


storage = RemoteStorage()


class Attachment(models.Model):
    """A model with an optional file, kept in a storage without local paths."""

    document = models.FileField(blank=True, storage=storage)

    class Meta:
        """Model metadata."""

        app_label = 'test'


# --- clean_files_delete_handler -------------------------------------------------------------------


def test_clean_files_delete_handler_skips_an_empty_file_field() -> None:
    """An instance without a file is deleted without the handler raising."""
    handlers.clean_files_delete_handler(Attachment(), signal=None, sender=Attachment)


def test_clean_files_delete_handler_removes_a_file_of_a_storage_without_paths() -> None:
    """The file is removed from a remote storage, which has no local path to test."""
    attachment = Attachment()
    attachment.document.save('report.txt', ContentFile(b'content'), save=False)
    name = attachment.document.name

    handlers.clean_files_delete_handler(attachment, signal=None, sender=Attachment)

    assert not storage.exists(name)
