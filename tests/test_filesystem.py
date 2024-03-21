from __future__ import annotations

from pathlib import Path
from unittest import mock

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


# def test_copy_recursive(tmp_path: Path) -> None:
#     raise NotImplementedError()
#     source_path = Path(__file__).parent
#     filesystem.copy_recursive(source_path, tmp_path)
#     raise ValueError(list(filesystem.find_recursive(tmp_path, "*.py")))
