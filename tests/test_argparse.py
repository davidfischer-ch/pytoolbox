from __future__ import annotations

from pathlib import Path
from typing import no_type_check
from unittest.mock import patch
import os

import pytest
from pytest import mark
from pytoolbox import argparse, exceptions, types


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


def test_full_paths_expands_tilde() -> None:
    """FullPaths expands ~ to the user home directory."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action=argparse.FullPaths)
    args = parser.parse_args(['~/some/dir'])
    assert args.path == Path('~/some/dir').expanduser().resolve()
    assert '~' not in str(args.path)


def test_full_paths_via_directory_arg() -> None:
    """DIRECTORY_ARG combo uses FullPaths + is_dir."""
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', **argparse.DIRECTORY_ARG)
    args = parser.parse_args(['/usr/lib'])
    assert args.directory == Path('/usr/lib').resolve()


def test_full_paths_via_file_arg() -> None:
    """FILE_ARG combo uses FullPaths + is_file."""
    parser = argparse.ArgumentParser()
    parser.add_argument('file', **argparse.FILE_ARG)
    args = parser.parse_args(['/etc/hosts'])
    assert args.file == Path('/etc/hosts').resolve()


# multiple -----------------------------------------------------------------------------------------


@mark.parametrize('input_val, expected', [
    ('hello', 'HELLO'),
    (['a', 'b'], ['A', 'B']),
    (('x', 'y'), ['X', 'Y'])
])
def test_multiple(input_val, expected) -> None:
    func = argparse.multiple(str.upper)
    assert func(input_val) == expected


# password -----------------------------------------------------------------------------------------


def test_password_with_value() -> None:
    assert argparse.password('secret') == 'secret'


def test_password_prompts_when_empty() -> None:
    with patch('pytoolbox.argparse.getpass.getpass', return_value='prompted'):
        assert argparse.password(None) == 'prompted'
        assert argparse.password('') == 'prompted'


# Range --------------------------------------------------------------------------------------------


def test_range_valid() -> None:
    r = argparse.Range(int, 0, 10)
    assert r(5) == 5
    assert r('7') == 7
    assert r(0) == 0
    assert r(10) == 10


def test_range_out_of_bounds() -> None:
    r = argparse.Range(int, 0, 10)
    with pytest.raises(argparse.ArgumentTypeError, match='Must be in range'):
        r(11)
    with pytest.raises(argparse.ArgumentTypeError, match='Must be in range'):
        r(-1)


def test_range_invalid_type() -> None:
    r = argparse.Range(int, 0, 10)
    with pytest.raises(argparse.ArgumentTypeError, match='Must be of type int'):
        r('abc')


def test_range_float() -> None:
    r = argparse.Range(float, 0.0, 1.0)
    assert r('0.5') == 0.5
    with pytest.raises(argparse.ArgumentTypeError, match='Must be in range'):
        r('1.5')


# ActionArgumentParser -----------------------------------------------------------------------------


def test_action_argument_parser_no_args() -> None:
    parser = argparse.ActionArgumentParser()
    parser.add_action('do', lambda args: None)
    with pytest.raises(SystemExit, match='An action is required'):
        parser.execute([])


def test_action_argument_parser_version(capsys) -> None:
    parser = argparse.ActionArgumentParser(version='1.2.3')
    parser.execute(['version'])
    assert capsys.readouterr().out.strip() == '1.2.3'


def test_action_argument_parser_handle_called_process_error() -> None:
    def failing(args):
        raise exceptions.CalledProcessError(cmd=['test'], returncode=1)

    parser = argparse.ActionArgumentParser()
    parser.add_action('fail', failing)
    with pytest.raises(SystemExit):
        parser.execute(['fail'])


def test_action_argument_parser_handle_message_mixin() -> None:
    class CustomError(exceptions.MessageMixin):
        message = 'Something went wrong'

    def failing(args):
        raise CustomError()

    parser = argparse.ActionArgumentParser()
    parser.add_action('fail', failing)
    with pytest.raises(SystemExit):
        parser.execute(['fail'])


def test_action_argument_parser_unhandled_exception() -> None:
    def failing(args):
        raise ValueError('unexpected')

    parser = argparse.ActionArgumentParser()
    parser.add_action('fail', failing)
    with pytest.raises(ValueError, match='unexpected'):
        parser.execute(['fail'])


# ArgumentParser -----------------------------------------------------------------------------------


def test_argument_parser_registers_actions() -> None:
    """ArgumentParser registers 'chain' and 'fullpaths' actions."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action='fullpaths')
    args = parser.parse_args(['/usr/lib'])
    assert args.path == Path('/usr/lib').resolve()


# env_default --------------------------------------------------------------------------------------


@mark.parametrize('env, name, expected', [
    ({'SOME': ''}, 'SOME', {'default': ''}),
    ({'SOME': 'value'}, 'SOME', {'default': 'value'}),
    ({'SOME': ''}, 'OTHER', {'required': True})
])
def test_env_default(env, name, expected):
    with patch.dict(os.environ, env, clear=True):
        assert argparse.env_default(name) == expected
