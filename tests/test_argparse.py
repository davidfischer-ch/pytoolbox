import argparse, os

from pytest import raises
from pytoolbox import types
from pytoolbox.argparse import is_dir, is_file, FullPaths


def test_is_dir():
    assert is_dir('/home') == '/home'
    with raises(argparse.ArgumentTypeError):
        is_dir('sjdsajkd')


def test_is_file():
    assert is_file('/etc/hosts') == '/etc/hosts'
    with raises(argparse.ArgumentTypeError):
        is_file('wdjiwdji')


def test_full_paths():
    namespace = types.DummyObject()
    multi = FullPaths(None, 'multi')
    multi(None, namespace, ['a', 'b'])
    single = FullPaths(None, 'single')
    single(None, namespace, 'c')
    assert namespace.multi == [os.path.abspath(e) for e in ('a', 'b')]  # pylint:disable=no-member
    assert namespace.single == os.path.abspath('c')                     # pylint:disable=no-member
