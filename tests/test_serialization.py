import math, os

from pytest import raises
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


def test_PickleableObject():
    p1 = MyPoint(name='My point', x=6, y=-3)
    p1.write('test.pkl')
    p2 = MyPoint.read('test.pkl', store_path=True)
    assert p2.__dict__ == {'y': -3, 'x': 6, '_pickle_path': 'test.pkl', 'name': 'My point'}
    p2.write()
    p2.write('test2.pkl')
    os.remove('test.pkl')
    os.remove('test2.pkl')
    p2.write()
    assert os.path.exists('test2.pkl') is False
    assert p2._pickle_path == 'test.pkl'
    os.remove('test.pkl')

    p2.write('test2.pkl', store_path=True)
    assert os.path.exists('test.pkl') is False
    assert p2._pickle_path == 'test2.pkl'
    del p2._pickle_path
    with raises(ValueError):
        p2.write()
    os.remove('test2.pkl')
    filesystem.remove('test3.pkl')

    p3 = MyPoint.read(
        'test3.pkl',
        store_path=True,
        create_if_error=True,
        name='Default point',
        x=3,
        y=-6)
    p3.__dict__ == {'x': 3, 'y': -6, '_pickle_path': 'test3.pkl', 'name': 'Default point'}

    os.remove('test3.pkl')
    with raises(IOError):
        MyPoint.read('test3.pkl')
