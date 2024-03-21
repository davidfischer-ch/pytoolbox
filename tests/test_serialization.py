from __future__ import annotations

import math
import os

import pytest
from pytoolbox import filesystem
from pytoolbox.serialization import PickleableObject


class MyPoint(PickleableObject):

    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)


def test_pickleable_object() -> None:
    point_1 = MyPoint(name='My point', x=6, y=-3)
    point_1.write('test.pkl')
    point_2 = MyPoint.read('test.pkl', store_path=True)
    assert point_2.__dict__ == {'y': -3, 'x': 6, '_pickle_path': 'test.pkl', 'name': 'My point'}
    point_2.write()
    point_2.write('test2.pkl')
    os.remove('test.pkl')
    os.remove('test2.pkl')
    point_2.write()
    assert os.path.exists('test2.pkl') is False
    assert point_2._pickle_path == 'test.pkl'  # pylint:disable=protected-access
    os.remove('test.pkl')

    point_2.write('test2.pkl', store_path=True)
    assert os.path.exists('test.pkl') is False
    assert point_2._pickle_path == 'test2.pkl'  # pylint:disable=protected-access
    del point_2._pickle_path
    with pytest.raises(ValueError):
        point_2.write()
    os.remove('test2.pkl')
    filesystem.remove('test3.pkl')

    point_3 = MyPoint.read(
        'test3.pkl',
        store_path=True,
        create_if_error=True,
        name='Default point',
        x=3,
        y=-6)
    assert point_3.__dict__ == {
        'x': 3,
        'y': -6,
        '_pickle_path': 'test3.pkl',
        'name': 'Default point'
    }

    os.remove('test3.pkl')
    with pytest.raises(IOError):
        MyPoint.read('test3.pkl')
