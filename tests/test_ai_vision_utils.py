"""Tests for the ai.vision.utils module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from pytoolbox.network import http

# OpenCV has no wheel for every Python the suite runs on, and the download helpers never call it.
sys.modules.setdefault('cv2', mock.Mock())

from pytoolbox.ai.vision import utils  # noqa: E402  # pylint: disable=wrong-import-position


def test_load_to_file_ignores_a_file_planted_in_the_shared_temporary_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A file another user left in the shared temporary directory is never loaded as a download."""
    monkeypatch.setattr(tempfile, 'tempdir', str(tmp_path))
    (tmp_path / 'model.dat').write_bytes(b'planted')

    with mock.patch.object(http, 'iter_download_core', return_value=[(10, 10, b'downloaded')]):
        path = utils.load_to_file('http://example.com/model.dat')

    assert Path(path).read_bytes() == b'downloaded'


def test_load_to_file_refuses_a_cache_directory_open_to_others(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A cache directory another user can write to is refused, nothing downloaded into it."""
    monkeypatch.setattr(tempfile, 'tempdir', str(tmp_path))
    with mock.patch.object(http, 'iter_download_core', return_value=[(10, 10, b'downloaded')]):
        directory = Path(utils.load_to_file('http://example.com/model.dat')).parent
    directory.chmod(0o777)

    with (
        mock.patch.object(http, 'iter_download_core') as iter_download_core,
        pytest.raises(PermissionError),
    ):
        utils.load_to_file('http://example.com/other.dat')

    iter_download_core.assert_not_called()
