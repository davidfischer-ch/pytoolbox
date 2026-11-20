"""Tests for the virtualenv module."""

# pylint: disable=use-implicit-booleaness-not-comparison
from __future__ import annotations

import py_compile
from pathlib import Path

from pytoolbox import filesystem, virtualenv


def test_relocate_keeps_links_and_removes_the_bytecode(tmp_path: Path) -> None:
    """Relocating never writes through a link, and leaves no bytecode compiled for the old path."""
    source = tmp_path / 'source-environment'
    interpreter = tmp_path / 'interpreter'
    interpreter.write_bytes(b'built in ' + str(source).encode())
    interpreter.chmod(0o444)
    filesystem.makedirs(source / 'bin')
    (source / 'bin' / 'python').symlink_to(interpreter)
    filesystem.makedirs(source / 'lib')
    (source / 'lib' / 'module.py').write_text('VALUE = 1\n', encoding='utf-8')
    py_compile.compile(
        str(source / 'lib' / 'module.py'),
        cfile=str(source / 'lib' / 'module.pyc'),
        doraise=True,
    )

    virtualenv.relocate(source, tmp_path / 'env')

    assert (tmp_path / 'env' / 'bin' / 'python').readlink() == interpreter
    assert interpreter.read_bytes() == b'built in ' + str(source).encode()
    assert list(filesystem.find_recursive(tmp_path / 'env', '*.pyc')) == []


def test_relocate_rewrites_text_and_leaves_binaries_untouched(tmp_path: Path) -> None:
    """Relocating rewrites the paths in scripts, never in a binary, which a rewrite breaks."""
    source = tmp_path / 'source-environment'
    binary = b'\x7fELF\x02\x01\x01\x00' + str(source).encode() + b'/lib\x00\x00'
    filesystem.makedirs(source / 'bin')
    filesystem.makedirs(source / 'src')
    (source / 'bin' / 'python').write_bytes(binary)
    (source / 'src' / 'extension.so').write_bytes(binary)
    (source / 'bin' / 'tool').write_text(f'#!{source}/bin/python\n', encoding='utf-8')

    environment = tmp_path / 'env'
    virtualenv.relocate(source, environment)

    assert (environment / 'bin' / 'tool').read_text(encoding='utf-8') == (
        f'#!{environment}/bin/python\n'
    )
    assert (environment / 'bin' / 'python').read_bytes() == binary
    assert (environment / 'src' / 'extension.so').read_bytes() == binary
