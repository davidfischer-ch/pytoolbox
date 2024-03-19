from __future__ import annotations

from pathlib import Path
from typing import no_type_check
import argparse

import pytest
from pytoolbox import types
from pytoolbox.argparse import is_dir, is_file, FullPaths


def test_is_dir() -> None:
    assert is_dir('/home') == Path('/home')
    assert is_dir(Path('/home')) == Path('/home')
    with pytest.raises(argparse.ArgumentTypeError):
        is_dir('sjdsajkd')


def test_is_file() -> None:
    assert is_file('/etc/hosts') == Path('/etc/hosts')
    assert is_file(Path('/etc/hosts')) == Path('/etc/hosts')
    with pytest.raises(argparse.ArgumentTypeError):
        is_file('wdjiwdji')


@no_type_check
def test_full_paths() -> None:
    namespace = types.DummyObject()
    multi = FullPaths(None, 'multi')
    multi(None, namespace, ['a', 'b'])
    single = FullPaths(None, 'single')
    single(None, namespace, 'c')
    assert namespace.multi == [Path(e).resolve() for e in ('a', 'b')]  # pylint:disable=no-member
    assert namespace.single == Path('c').resolve()                     # pylint:disable=no-member
