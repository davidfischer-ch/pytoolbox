# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox.collections import pygal_deque

from . import base


class TestCollections(base.TestCase):

    tags = ('collections', )

    def test_pygal_deque(self):
        p = pygal_deque(maxlen=4)

        p.append(5)
        self.list_equal(p.list(fill=False), [5])
        p.append(5)
        p.append(5)
        self.list_equal(p.list(fill=False), [5, None, 5])
        p.append(5)
        self.list_equal(p.list(fill=False), [5, None, None, 5])
        p.append(5)
        self.list_equal(p.list(fill=False), [5, None, None, 5])
        p.append(None)
        self.list_equal(p.list(fill=False), [5, None, None, 5])
        p.append(None)
        self.list_equal(p.list(fill=False), [5, None, None, 5])
        p.append(5)
        self.list_equal(p.list(fill=False), [5, None, None, 5])
        self.list_equal(p.list(fill=True), [5, 5, 5, 5])
        p.append(1)
        self.list_equal(p.list(fill=False), [5, None, 5, 1])
        p.append(None)
        self.list_equal(p.list(fill=False), [5, 5, 1, 1])
        p.append(None)
        self.list_equal(p.list(fill=False), [5, 1, None, 1])
        self.list_equal(p.list(fill=True), [5, 1, 1, 1])
        p.append(None)
        self.list_equal(p.list(fill=False), [1, None, None, 1])
        p.append(2)
        p.append(3)
        self.list_equal(p.list(fill=False), [1, 1, 2, 3])
        p.append(None)
        p.append(2)
        self.list_equal(p.list(fill=False), [2, 3, 3, 2])
