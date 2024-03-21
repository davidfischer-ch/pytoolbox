from __future__ import annotations

from pathlib import Path
from unittest import mock

from pytest import mark

from pytoolbox import filesystem


def test_chown(tmp_path: Path) -> None:
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

    chown.assert_has_calls([
        mock.call(tmp_path, 100, 0),
        mock.call(file_b, 100, 0),
        mock.call(file_a, 100, 0),
        mock.call(file_c.parent, 100, 0),
        mock.call(file_c, 100, 0),
    ], any_order=True)


def test_copy_recursive(tmp_path: Path) -> None:
    src_path = Path(__file__).parent.parent / 'pytoolbox'
    stats = filesystem.copy_recursive(src_path, tmp_path, ["*/camera.py", "*/ffmpeg.py"])
    assert stats['src_size'] >= 6529  # Expect code to not shrink
    camera = 'multimedia/exif/camera.py'
    ffmpeg = 'multimedia/ffmpeg/ffmpeg.py'
    assert list(filesystem.find_recursive(tmp_path, "*")) == [tmp_path / camera, tmp_path / ffmpeg]
    assert (tmp_path / camera).read_bytes() == (src_path / camera).read_bytes()
    assert (tmp_path / ffmpeg).read_bytes() == (src_path / ffmpeg).read_bytes()


@mark.parametrize('chunk_size', [77, 50 * 1024 * 1024])
def test_copy_recursive_chunk_size(small_mp4: Path, tmp_path: Path, chunk_size: int) -> None:
    """Ensure chunk_size doesn't influence the copy (corrupting files)."""
    assert filesystem.copy_recursive(
        source_path=small_mp4.parent,
        destination_path=tmp_path,
        patterns=f"*/{small_mp4.name}",
        chunk_size=chunk_size
    )['src_size'] == 383631  # small.mp4 size
    assert list(filesystem.find_recursive(tmp_path, "*")) == [tmp_path / small_mp4.name]
    assert (tmp_path / small_mp4.name).read_bytes() == small_mp4.read_bytes()


def test_copy_recursive_missing(tmp_path: Path) -> None:
    # pylint:disable=use-implicit-booleaness-not-comparison
    assert filesystem.copy_recursive(tmp_path / 'missing', tmp_path / 'target')['src_size'] == 0
    assert list(filesystem.find_recursive(tmp_path / 'target', "*")) == []
