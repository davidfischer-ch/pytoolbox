# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse, os

from pytoolbox import types
from pytoolbox.argparse import is_dir, is_file, FullPaths

from . import base


class TestArgparse(base.TestCase):

    tags = ('argparse', )

    def test_is_dir(self):
        self.equal(is_dir('/home'), '/home')
        with self.raises(argparse.ArgumentTypeError):
            is_dir('sjdsajkd')

    def test_is_file(self):
        self.equal(is_file('/etc/hosts'), '/etc/hosts')
        with self.raises(argparse.ArgumentTypeError):
            is_file('wdjiwdji')

    def test_full_paths(self):
        namespace = types.DummyObject()
        multi = FullPaths(None, 'multi')
        multi(None, namespace, ['a', 'b'])
        single = FullPaths(None, 'single')
        single(None, namespace, 'c')
        self.list_equal(namespace.multi, [os.path.abspath(e) for e in ('a', 'b')])
        self.equal(namespace.single, os.path.abspath('c'))
