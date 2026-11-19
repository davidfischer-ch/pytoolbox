"""Tests for the serialization module."""

# pylint:disable=protected-access
from __future__ import annotations

import math
import os
import stat
from collections.abc import Iterator
from pathlib import Path

import pytest

from pytoolbox import filesystem, serialization


class MyPoint(serialization.PickleableObject):
    """Test point class for PickleableObject tests."""

    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        """Return the Euclidean length of the point from the origin."""
        return math.sqrt(self.x * self.x + self.y * self.y)


@pytest.fixture
def usual_umask() -> Iterator[None]:
    """Run the test under the usual umask, which lets the group and the others read a new file."""
    previous = os.umask(0o022)
    yield
    os.umask(previous)


def test_pickleable_object() -> None:
    """PickleableObject can write and read itself from pickle files."""
    point_1 = MyPoint(name='My point', x=6, y=-3)
    point_1.write('test.pkl')
    point_2 = MyPoint.read('test.pkl', store_path=True)
    assert point_2.__dict__ == {'y': -3, 'x': 6, '_pickle_path': 'test.pkl', 'name': 'My point'}
    point_2.write()
    point_2.write('test2.pkl')
    Path('test.pkl').unlink()
    Path('test2.pkl').unlink()
    point_2.write()
    assert Path('test2.pkl').exists() is False
    assert point_2._pickle_path == 'test.pkl'
    Path('test.pkl').unlink()

    point_2.write('test2.pkl', store_path=True)
    assert Path('test.pkl').exists() is False
    assert point_2._pickle_path == 'test2.pkl'
    del point_2._pickle_path
    with pytest.raises(ValueError):
        point_2.write()
    Path('test2.pkl').unlink()
    filesystem.remove('test3.pkl')

    point_3 = MyPoint.read(
        'test3.pkl',
        store_path=True,
        create_if_error=True,
        name='Default point',
        x=3,
        y=-6,
    )
    assert point_3.__dict__ == {
        'x': 3,
        'y': -6,
        '_pickle_path': 'test3.pkl',
        'name': 'Default point',
    }

    Path('test3.pkl').unlink()
    with pytest.raises(OSError):
        MyPoint.read('test3.pkl')


@pytest.mark.usefixtures('usual_umask')
def test_to_file_safe_keeps_the_mode_of_the_target(tmp_path: Path) -> None:
    """A private file stays private once safely rewritten."""
    path = tmp_path / 'secrets.yaml'
    path.write_text('old', encoding='utf-8')
    path.chmod(0o600)

    serialization.to_file(str(path), data='new', safe=True)

    assert path.read_text(encoding='utf-8') == 'new'
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.usefixtures('usual_umask')
def test_to_file_safe_writes_through_a_symbolic_link(tmp_path: Path) -> None:
    """A symbolic link stays in place, its target receives the data and keeps its mode."""
    target = tmp_path / 'real.yaml'
    target.write_text('old', encoding='utf-8')
    target.chmod(0o600)
    link = tmp_path / 'link.yaml'
    link.symlink_to(target)

    serialization.to_file(str(link), data='new', safe=True)

    assert link.is_symlink()
    assert target.read_text(encoding='utf-8') == 'new'
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_to_file_safe_leaves_the_directory_as_it_was_when_the_write_fails(tmp_path: Path) -> None:
    """A failed write leaves no partial file behind and spares the file of another writer."""
    path = tmp_path / 'data.txt'
    path.write_text('old', encoding='utf-8')
    other = tmp_path / 'data.txt.tmp'
    other.write_text('another writer', encoding='utf-8')

    with pytest.raises(TypeError):
        serialization.to_file(str(path), data=object(), safe=True)

    assert path.read_text(encoding='utf-8') == 'old'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['data.txt', 'data.txt.tmp']
    assert other.read_text(encoding='utf-8') == 'another writer'
