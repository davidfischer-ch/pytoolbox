"""Tests for the filesystem module."""

# pylint:disable=use-implicit-booleaness-not-comparison
from __future__ import annotations

import errno
import os
import re
import stat
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
    chown.assert_called_once_with(file_a, 0, -1, follow_symlinks=True)

    with mock.patch('os.chown') as chown:
        filesystem.chown(tmp_path, 100, 'root')
    chown.assert_called_once_with(tmp_path, 100, 0, follow_symlinks=True)

    with mock.patch('os.chown') as chown:
        filesystem.chown(tmp_path, 100, 'root', recursive=True)

    chown.assert_has_calls(
        [
            mock.call(tmp_path, 100, 0, follow_symlinks=True),
            mock.call(file_b, 100, 0, follow_symlinks=False),
            mock.call(file_a, 100, 0, follow_symlinks=False),
            mock.call(file_c.parent, 100, 0, follow_symlinks=True),
            mock.call(file_c, 100, 0, follow_symlinks=False),
        ],
        any_order=True,
    )


@mark.skipif(sys.platform == 'win32', reason='os.chown is POSIX only')
def test_chown_recursive_changes_a_link_not_its_target(tmp_path: Path) -> None:
    """Without follow_symlinks, a link in the tree is changed itself, its target outside never."""
    (tmp_path / 'outside.txt').touch()
    tree = tmp_path / 'tree'
    filesystem.makedirs(tree)
    (tree / 'link').symlink_to(tmp_path / 'outside.txt')

    with mock.patch('os.chown') as chown:
        filesystem.chown(tree, 100, recursive=True)

    assert mock.call(tree / 'link', 100, -1, follow_symlinks=False) in chown.call_args_list


def _strict_chown(path: Path, _uid: int, _gid: int, *, follow_symlinks: bool = True) -> None:
    """Mimic real os.chown: raise FileNotFoundError on broken symlinks it follows."""
    if follow_symlinks and Path(path).is_symlink() and not Path(path).exists():
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


def test_copy_recursive_copies_an_empty_file(tmp_path: Path) -> None:
    """An empty source, of size 0, is copied as a complete one."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (source / 'empty.txt').touch()

    assert filesystem.copy_recursive(source, tmp_path / 'destination')['src_size'] == 0
    assert (tmp_path / 'destination' / 'empty.txt').read_bytes() == b''


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


def test_copy_recursive_reports_its_progress(tmp_path: Path) -> None:
    """The progress callback is called with the ratio copied, up to the whole source."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (source / 'a.txt').write_text('a' * 10, encoding='utf-8')
    ratios: list[float] = []

    filesystem.copy_recursive(
        source,
        tmp_path / 'destination',
        chunk_size=4,
        progress_callback=lambda **kwargs: ratios.append(kwargs['ratio']),
        ratio_delta=-1,
        time_delta=-1,
    )

    assert ratios == [0.0, 0.4, 0.8, 1.0]


def test_copy_recursive_raises_on_a_size_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A copy whose files do not sum to the size of the source raises, and removes what it wrote."""
    source = tmp_path / 'source'
    filesystem.makedirs(source)
    (source / 'a.txt').write_text('abc', encoding='utf-8')
    monkeypatch.setattr(filesystem, 'get_size', lambda **kwargs: 4)

    with pytest.raises(OSError, match=r'\(4 vs 3\)'):
        filesystem.copy_recursive(source, tmp_path / 'destination')
    assert not (tmp_path / 'destination' / 'a.txt').exists()


def test_copy_recursive_missing(tmp_path: Path) -> None:
    """copy_recursive() returns zero size when source is missing."""
    assert filesystem.copy_recursive(tmp_path / 'missing', tmp_path / 'target')['src_size'] == 0
    assert list(filesystem.find_recursive(tmp_path / 'target', '*')) == []


def test_open_safely_replaces_the_target_only_on_success(tmp_path: Path) -> None:
    """The target changes only once the write succeeds; a failed one leaves nothing beside it."""
    target = tmp_path / 'data.bin'
    target.write_bytes(b'old')

    with pytest.raises(RuntimeError), filesystem.open_safely(target) as f:
        f.write(b'partial')
        raise RuntimeError('write failed')

    assert target.read_bytes() == b'old'
    assert list(tmp_path.iterdir()) == [target]

    with filesystem.open_safely(target) as f:
        f.write(b'new')
        assert target.read_bytes() == b'old'

    assert target.read_bytes() == b'new'
    assert list(tmp_path.iterdir()) == [target]


@mark.skipif(not Path('/proc/self/fd').is_dir(), reason='lists open descriptors through /proc')
def test_open_safely_refusing_a_mode_leaves_no_descriptor_nor_file(tmp_path: Path) -> None:
    """An invalid mode raises, with no descriptor left open and no file beside the target."""
    target = tmp_path / 'data.bin'
    descriptors = len(list(Path('/proc/self/fd').iterdir()))

    with pytest.raises(ValueError), filesystem.open_safely(target, 'wz'):
        pass

    assert len(list(Path('/proc/self/fd').iterdir())) == descriptors
    assert list(tmp_path.iterdir()) == []


def test_open_safely_keeps_the_mode_of_the_target(tmp_path: Path) -> None:
    """A private target stays private once rewritten, whatever mode the umask gives a new file."""
    target = tmp_path / 'secret.bin'
    target.write_bytes(b'old')
    target.chmod(0o600)
    previous_umask = os.umask(0o022)
    try:
        with filesystem.open_safely(target) as f:
            f.write(b'new')
    finally:
        os.umask(previous_umask)

    assert target.read_bytes() == b'new'
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


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


def test_temp_storage_create_tmp_directory_refuses_an_existing_path(tmp_path: Path) -> None:
    """A directory already there is neither adopted nor removed with the temporary paths."""
    tmp = filesystem.TempStorage(root=tmp_path)
    filesystem.makedirs(tmp_path / 'work')
    (tmp_path / 'work' / 'keep.txt').write_text('kept', encoding='utf-8')

    with pytest.raises(FileExistsError):
        tmp.create_tmp_directory('work')
    tmp.remove_all()

    assert (tmp_path / 'work' / 'keep.txt').read_text(encoding='utf-8') == 'kept'


def test_temp_storage_create_tmp_file_refuses_a_link(tmp_path: Path) -> None:
    """A link already at the path is never written through, nor removed with the temporary paths."""
    tmp = filesystem.TempStorage(root=tmp_path)
    (tmp_path / 'victim.txt').write_text('victim', encoding='utf-8')
    (tmp_path / 'job.txt').symlink_to(tmp_path / 'victim.txt')

    with pytest.raises(FileExistsError):
        tmp.create_tmp_file(name='job', extension='txt')
    tmp.remove_all()

    assert (tmp_path / 'job.txt').is_symlink()
    assert (tmp_path / 'victim.txt').read_text(encoding='utf-8') == 'victim'


def test_temp_storage_creates_private_paths(tmp_path: Path) -> None:
    """Temporary files and directories are private to their owner, as tempfile makes them."""
    with filesystem.TempStorage(root=tmp_path) as tmp:
        assert stat.S_IMODE(tmp.create_tmp_directory().stat().st_mode) == 0o700
        assert stat.S_IMODE(tmp.create_tmp_file(return_file=False).stat().st_mode) == 0o600
