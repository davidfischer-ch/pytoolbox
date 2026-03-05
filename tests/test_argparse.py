from __future__ import annotations

from pathlib import Path
from typing import no_type_check
from unittest.mock import patch
import os

import pytest
from pytest import mark
from pytoolbox import argparse, types


def test_is_dir() -> None:
    assert argparse.is_dir('/home') == Path('/home')
    assert argparse.is_dir(Path('/home')) == Path('/home')
    with pytest.raises(argparse.ArgumentTypeError):
        argparse.is_dir('sjdsajkd')


def test_is_file() -> None:
    assert argparse.is_file('/etc/hosts') == Path('/etc/hosts')
    assert argparse.is_file(Path('/etc/hosts')) == Path('/etc/hosts')
    with pytest.raises(argparse.ArgumentTypeError):
        argparse.is_file('wdjiwdji')


@no_type_check
def test_full_paths() -> None:
    namespace = types.DummyObject()
    multi = argparse.FullPaths(None, 'multi')
    multi(None, namespace, ['a', 'b'])
    single = argparse.FullPaths(None, 'single')
    single(None, namespace, 'c')
    assert namespace.multi == [Path(e).resolve() for e in ('a', 'b')]  # pylint:disable=no-member
    assert namespace.single == Path('c').resolve()                     # pylint:disable=no-member


@no_type_check
def test_full_paths_none_skipped() -> None:
    """With nargs='?' argparse passes None when the argument is omitted."""
    namespace = types.DummyObject()
    action = argparse.FullPaths(None, 'path')
    action(None, namespace, None)
    assert namespace.path is None  # pylint:disable=no-member


def test_full_paths_nargs_optional_flag() -> None:
    """FullPaths with nargs='?' on an optional flag."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', action=argparse.FullPaths, nargs='?')
    # Omitted optional argument
    args = parser.parse_args([])
    assert args.path is None
    # Provided optional argument
    args = parser.parse_args(['--path', '/usr/lib'])
    assert args.path == Path('/usr/lib').resolve()


def test_full_paths_nargs_optional_positional() -> None:
    """FullPaths with nargs='?' on a positional argument."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action=argparse.FullPaths, nargs='?')
    # Omitted positional argument
    args = parser.parse_args([])
    assert args.path is None
    # Provided positional argument
    args = parser.parse_args(['/usr/lib'])
    assert args.path == Path('/usr/lib').resolve()


@mark.parametrize(('sep', 'arguments', 'expected'), [

    (None, ['some'], None),
    (None, ['some', '--patterns', ''], []),
    (None, ['some', '--patterns', 'a'], ['a']),
    (None, ['some', '--patterns', 'a', 'b', 'c d  '], ['a', 'b', 'c d']),
    (None, ['some', '--patterns', 'a', '--patterns', ' b  '], ['a', 'b']),
    (None, ['some', '--patterns', 'a', '--patterns', 'b', 'c d  e'], ['a', 'b', 'c d  e']),

    (' ', ['some'], None),
    (' ', ['some', '--patterns', ''], []),
    (' ', ['some', '--patterns', 'a'], ['a']),
    (' ', ['some', '--patterns', 'a', 'b', 'c d  '], ['a', 'b', 'c', 'd']),
    (' ', ['some', '--patterns', 'a', '--patterns', ' b  '], ['a', 'b']),
    (' ', ['some', '--patterns', 'a', '--patterns', 'b', 'c d  e'], ['a', 'b', 'c', 'd', 'e']),

    (',', ['some'], None),
    (',', ['some', '--patterns', ''], []),
    (',', ['some', '--patterns', 'a'], ['a']),
    (',', ['some', '--patterns', 'a', 'b', 'c, d , '], ['a', 'b', 'c', 'd']),
    (',', ['some', '--patterns', 'a', '--patterns', ' b  ,'], ['a', 'b']),
    (',', ['some', '--patterns', 'a', '--patterns', 'b', 'c, d,  ,e'], ['a', 'b', 'c', 'd', 'e']),

])
def test_chain_action(sep, arguments, expected):

    def action_some(args):
        assert args.patterns == expected

    parser = argparse.ActionArgumentParser(epilog='This is a test')
    arg = parser.add_action('some', action_some)
    arg('-p', '--patterns', **argparse.MULTI_ARG(sep))
    parser.execute(arguments)


@mark.parametrize('env, name, expected', [
    ({'SOME': ''}, 'SOME', {'default': ''}),
    ({'SOME': 'value'}, 'SOME', {'default': 'value'}),
    ({'SOME': ''}, 'OTHER', {'required': True})
])
def test_env_default(env, name, expected):
    with patch.dict(os.environ, env, clear=True):
        assert argparse.env_default(name) == expected
