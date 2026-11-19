"""Tests for the django.storage module."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from pytoolbox.django import storage

pytestmark = pytest.mark.filterwarnings('ignore:Overwrite.* is deprecated:DeprecationWarning')


def test_overwrite_file_system_storage_replaces_a_stored_file(tmp_path: Path) -> None:
    """A file saved under a stored name keeps that name and replaces the stored content."""
    store = storage.OverwriteFileSystemStorage(location=tmp_path)
    assert store.save('report.txt', ContentFile(b'first')) == 'report.txt'
    assert store.save('report.txt', ContentFile(b'second')) == 'report.txt'
    assert (tmp_path / 'report.txt').read_bytes() == b'second'
    assert [path.name for path in tmp_path.iterdir()] == ['report.txt']


def test_overwrite_file_system_storage_is_deprecated(tmp_path: Path) -> None:
    """Creating an OverwriteFileSystemStorage emits a DeprecationWarning naming its replacement."""
    with pytest.warns(DeprecationWarning, match='allow_overwrite=True'):
        storage.OverwriteFileSystemStorage(location=tmp_path)


def test_overwrite_mixin_subclass_is_deprecated() -> None:
    """Subclassing OverwriteMixin emits a DeprecationWarning naming its replacement."""
    with pytest.warns(DeprecationWarning, match='allow_overwrite=True'):

        class Storage(storage.OverwriteMixin, FileSystemStorage):  # pylint:disable=unused-variable
            """Storage overwriting its files."""


def test_overwrite_mixin_truncates_a_name_to_max_length(tmp_path: Path) -> None:
    """A name longer than max_length is cut to it, its extension kept."""

    class Storage(storage.OverwriteMixin, FileSystemStorage):
        """Storage overwriting its files."""

    name = Storage(location=tmp_path).get_available_name('a' * 20 + '.txt', max_length=16)
    assert len(name) <= 16
    assert name.endswith('.txt')


def test_overwrite_mixin_replaces_a_stored_file(tmp_path: Path) -> None:
    """Through the mixin, a file saved under a stored name keeps that name and replaces it."""

    class Storage(storage.OverwriteMixin, FileSystemStorage):
        """Storage overwriting its files."""

    store = Storage(location=tmp_path)
    assert store.save('report.txt', ContentFile(b'first')) == 'report.txt'
    assert store.save('report.txt', ContentFile(b'second')) == 'report.txt'
    assert (tmp_path / 'report.txt').read_bytes() == b'second'
