"""Tests for the serialization module."""

# pylint:disable=protected-access
from __future__ import annotations

import math
from pathlib import Path

import pytest

from pytoolbox import filesystem
from pytoolbox.serialization import PickleableObject


class MyPoint(PickleableObject):
    """Test point class for PickleableObject tests."""

    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        """Return the Euclidean length of the point from the origin."""
        return math.sqrt(self.x * self.x + self.y * self.y)


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
