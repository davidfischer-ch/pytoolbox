"""Tests for the filesystem module."""

# pylint:disable=use-implicit-booleaness-not-comparison
from __future__ import annotations

import errno
import os
import re
import sys
from pathlib import Path
from unittest import mock

import pytest
from pytest import mark

from pytoolbox import filesystem


@mark.skipif(sys.platform == 'win32', reason='os.chown is POSIX only')
def test_chown(tmp_path: Path) -> None:
    """chown() changes file ownership for user and/or group."""
    file_a = tmp_path / 'a.txt'
    file_b = tmp_path / 'b.txt'
    file_c = tmp_path / 'other' / 'c.txt'
    filesystem.makedirs(file_c, parent=True)
    Path(file_a).touch()
    Path(file_b).touch()
    Path(file_c).touch()

    with mock.patch('os.chown') as chown:
        filesystem.chown(file_a, 'root')
    chown.assert_called_once_with(file_a, 0, -1)

    with mock.patch('os.chown') as chown:
        filesystem.chown(tmp_path, 100, 'root')
    chown.assert_called_once_with(tmp_path, 100, 0)

    with mock.patch('os.chown') as chown:
        filesystem.chown(tmp_path, 100, 'root', recursive=True)

    chown.assert_has_calls(
        [
            mock.call(tmp_path, 100, 0),
            mock.call(file_b, 100, 0),
            mock.call(file_a, 100, 0),
            mock.call(file_c.parent, 100, 0),
            mock.call(file_c, 100, 0),
        ],
        any_order=True,
    )


def _strict_chown(path: Path, _uid: int, _gid: int) -> None:
    """Mimic real os.chown: raise FileNotFoundError on broken symlinks."""
    if Path(path).is_symlink() and not Path(path).exists():
        raise FileNotFoundError(2, 'No such file or directory', str(path))


@mark.skipif(sys.platform == 'win32', reason='os.chown is POSIX only')
def test_chown_broken_symlink(tmp_path: Path) -> None:
    """chown() must not raise on a broken symlink."""
    broken = tmp_path / 'broken'
    broken.symlink_to(tmp_path / 'missing')

    with mock.patch('os.chown', side_effect=_strict_chown):
        filesystem.chown(broken, 'root')  # must not raise


@mark.skipif(sys.platform == 'win32', reason='os.chown is POSIX only')
def test_chown_recursive_broken_symlink(tmp_path: Path) -> None:
    """chown() with recursive=True must not raise when a broken symlink is encountered."""
    (tmp_path / 'real.txt').touch()
    broken = tmp_path / 'broken'
    broken.symlink_to(tmp_path / 'missing')

    with mock.patch('os.chown', side_effect=_strict_chown):
        filesystem.chown(tmp_path, 'root', recursive=True)  # must not raise


def test_copy_recursive(tmp_path: Path) -> None:
    """copy_recursive() copies files matching patterns to destination."""
    src_path = Path(__file__).parent.parent / 'pytoolbox'
    stats = filesystem.copy_recursive(src_path, tmp_path, ['*/camera.py', '*/ffmpeg.py'])
    assert stats['src_size'] >= 6529  # Expect code to not shrink
    camera = 'multimedia/exif/camera.py'
    ffmpeg = 'multimedia/ffmpeg/ffmpeg.py'
    assert sorted(filesystem.find_recursive(tmp_path, '*')) == [
        tmp_path / camera,
        tmp_path / ffmpeg,
    ]
    assert (tmp_path / camera).read_bytes() == (src_path / camera).read_bytes()
    assert (tmp_path / ffmpeg).read_bytes() == (src_path / ffmpeg).read_bytes()


@mark.parametrize('chunk_size', [77, 50 * 1024 * 1024])
def test_copy_recursive_chunk_size(small_mp4: Path, tmp_path: Path, chunk_size: int) -> None:
    """Ensure chunk_size doesn't influence the copy (corrupting files)."""
    assert (
        filesystem.copy_recursive(
            source_path=small_mp4.parent,
            destination_path=tmp_path,
            patterns=f'*/{small_mp4.name}',
            chunk_size=chunk_size,
        )['src_size']
        == 383631
    )  # small.mp4 size
    assert list(filesystem.find_recursive(tmp_path, '*')) == [tmp_path / small_mp4.name]
    assert (tmp_path / small_mp4.name).read_bytes() == small_mp4.read_bytes()


def test_copy_recursive_into_a_directory_with_files_keeps_them(tmp_path: Path) -> None:
    """The size check covers the copied files, not the files the destination already held."""
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    filesystem.makedirs(source)
    filesystem.makedirs(destination)
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    (destination / 'keep.txt').write_text('kept!', encoding='utf-8')

    assert filesystem.copy_recursive(source, destination)['src_size'] == 3

    assert (destination / 'a.txt').read_text(encoding='utf-8') == 'abc'
    assert (destination / 'keep.txt').read_text(encoding='utf-8') == 'kept!'


def test_copy_recursive_copies_a_link_to_a_file_as_a_link(tmp_path: Path) -> None:
    """Without follow_symlinks, a link to a file outside the source never copies its content."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (tmp_path / 'secret.txt').write_text('secret', encoding='utf-8')
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    (source / 'link.txt').symlink_to(Path('..') / 'secret.txt')

    filesystem.copy_recursive(source, tmp_path / 'destination')

    link = tmp_path / 'destination' / 'link.txt'
    assert link.is_symlink()
    assert link.readlink() == Path('..') / 'secret.txt'
    assert (tmp_path / 'destination' / 'a.txt').read_text(encoding='utf-8') == 'abc'


def test_copy_recursive_copies_a_broken_link(tmp_path: Path) -> None:
    """A broken link in the source neither fails the copy nor removes the destination."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    (source / 'broken.txt').symlink_to(tmp_path / 'missing.txt')

    filesystem.copy_recursive(source, tmp_path / 'destination')

    assert (tmp_path / 'destination' / 'broken.txt').readlink() == tmp_path / 'missing.txt'
    assert (tmp_path / 'destination' / 'a.txt').read_text(encoding='utf-8') == 'abc'


def test_copy_recursive_replaces_a_link_in_the_destination(tmp_path: Path) -> None:
    """A file copied over a link in the destination replaces the link, never writes through it."""
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    filesystem.makedirs(source)
    filesystem.makedirs(destination)
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    (tmp_path / 'victim.txt').write_text('victim', encoding='utf-8')
    (destination / 'a.txt').symlink_to(tmp_path / 'victim.txt')

    filesystem.copy_recursive(source, destination)

    assert not (destination / 'a.txt').is_symlink()
    assert (destination / 'a.txt').read_text(encoding='utf-8') == 'abc'
    assert (tmp_path / 'victim.txt').read_text(encoding='utf-8') == 'victim'


@mark.skipif(os.geteuid() == 0, reason='root reads a file without read permission')
def test_copy_recursive_error_removes_only_what_it_created(tmp_path: Path) -> None:
    """A failed copy removes the files and directories it made, never the destination's others."""
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    filesystem.makedirs(source / 'sub' / 'deeper')
    filesystem.makedirs(destination)
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    (source / 'sub' / 'b.txt').write_text('def', encoding='utf-8')
    (source / 'sub' / 'deeper' / 'unreadable.txt').write_text('ghi', encoding='utf-8')
    (source / 'sub' / 'deeper' / 'unreadable.txt').chmod(0)
    (destination / 'keep.txt').write_text('kept!', encoding='utf-8')

    with pytest.raises(PermissionError):
        filesystem.copy_recursive(source, destination)

    assert sorted(destination.iterdir()) == [destination / 'keep.txt']
    assert (destination / 'keep.txt').read_text(encoding='utf-8') == 'kept!'


def test_copy_recursive_refuses_a_link_to_a_directory_in_the_destination(tmp_path: Path) -> None:
    """Without follow_symlinks, nothing is written through a link to a destination directory."""
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    outside = tmp_path / 'outside'
    filesystem.makedirs(source / 'sub')
    filesystem.makedirs(destination)
    filesystem.makedirs(outside)
    (source / 'sub' / 'a.txt').write_text('abc', encoding='utf-8')
    (destination / 'sub').symlink_to(outside)

    with pytest.raises(OSError) as error:
        filesystem.copy_recursive(source, destination)

    assert error.value.errno == errno.ELOOP
    assert list(outside.iterdir()) == []
    assert (destination / 'sub').readlink() == outside


def test_copy_recursive_follows_a_link_to_a_directory_when_asked(tmp_path: Path) -> None:
    """With follow_symlinks, a link to a directory in the destination is written through."""
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    outside = tmp_path / 'outside'
    filesystem.makedirs(source / 'sub')
    filesystem.makedirs(destination)
    filesystem.makedirs(outside)
    (source / 'sub' / 'a.txt').write_text('abc', encoding='utf-8')
    (destination / 'sub').symlink_to(outside)

    filesystem.copy_recursive(source, destination, follow_symlinks=True)

    assert (outside / 'a.txt').read_text(encoding='utf-8') == 'abc'


def test_copy_recursive_error_before_the_copy_surfaces_as_itself(tmp_path: Path) -> None:
    """An error raised before any file is copied reaches the caller, never masked by the cleanup."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (source / 'a.txt').write_text('abc', encoding='utf-8')

    with pytest.raises(re.error):
        filesystem.copy_recursive(source, tmp_path / 'destination', '(', regex=True)


def test_copy_recursive_missing(tmp_path: Path) -> None:
    """copy_recursive() returns zero size when source is missing."""
    assert filesystem.copy_recursive(tmp_path / 'missing', tmp_path / 'target')['src_size'] == 0
    assert list(filesystem.find_recursive(tmp_path / 'target', '*')) == []


def test_remove_directory_recursive(tmp_path: Path) -> None:
    """remove() with recursive=True should handle directories."""
    directory = tmp_path / 'subdir'
    directory.mkdir()
    (directory / 'file.txt').write_text('hello')
    assert filesystem.remove(directory, recursive=True) is True
    assert not directory.exists()


def test_symlink_over_a_regular_file_to_a_missing_source_reports_it_exists(tmp_path: Path) -> None:
    """A link name taken by a regular file raises EEXIST, also when the source is missing."""
    link_name = tmp_path / 'taken'
    link_name.write_text('a regular file')

    with pytest.raises(OSError) as error:
        filesystem.symlink(str(tmp_path / 'missing'), str(link_name))

    assert error.value.errno == errno.EEXIST
