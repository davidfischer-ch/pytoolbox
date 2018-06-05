# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import math, os

from pytoolbox.encoding import csv_reader
from pytoolbox.filesystem import remove
from pytoolbox.serialization import PickleableObject

from . import base

here = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
here = os.path.join(here, '../../..' if 'build/lib' in here else '..', 'tests')


class MyPoint(PickleableObject):

    def __init__(self, name=None, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y

    @property
    def length(self):
        return math.sqrt(self.x*self.x + self.y*self.y)


class TestSerialization(base.TestCase):

    tags = ('serialization', )

    def test_PickleableObject(self):
        p1 = MyPoint(name='My point', x=6, y=-3)
        p1.write('test.pkl')
        p2 = MyPoint.read('test.pkl', store_path=True)
        self.dict_equal(p2.__dict__, {'y': -3, 'x': 6, '_pickle_path': 'test.pkl', 'name': 'My point'})
        p2.write()
        p2.write('test2.pkl')
        os.remove('test.pkl')
        os.remove('test2.pkl')
        p2.write()
        self.false(os.path.exists('test2.pkl'))
        self.equal(p2._pickle_path, 'test.pkl')
        os.remove('test.pkl')
        p2.write('test2.pkl', store_path=True)
        self.false(os.path.exists('test.pkl'))
        self.equal(p2._pickle_path, 'test2.pkl')
        del p2._pickle_path
        with self.raises(ValueError):
            p2.write()
        os.remove('test2.pkl')
        remove('test3.pkl')
        p3 = MyPoint.read('test3.pkl', store_path=True, create_if_error=True, name='Default point', x=3, y=-6)
        self.dict_equal(p3.__dict__, {'x': 3, 'y': -6, '_pickle_path': 'test3.pkl', 'name': 'Default point'})
        os.remove('test3.pkl')
        with self.raises(IOError):
            MyPoint.read('test3.pkl')

    def test_csv_reader(self):
        values, i = [('David', 'Vélo'), ('Michaël', 'Tennis de table'), ('Loïc', 'Piano')], 0
        for name, hobby in csv_reader(os.path.join(here, 'unicode.csv')):
            self.tuple_equal((name, hobby), values[i])
            i += 1
