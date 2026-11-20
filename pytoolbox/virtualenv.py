"""
Python virtual environment relocation utilities.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Final

from .filesystem import find_recursive
from .subprocess import rsync

__all__ = ['BINARY_HEAD_SIZE', 'BINARY_MAGICS', 'relocate']

#: Size of the head read from a file to distinguish a binary, in bytes.
BINARY_HEAD_SIZE: Final[int] = 8192

#: Magic numbers of the executables and libraries: ELF, then Mach-O (32, 64 bits, both orders, fat).
BINARY_MAGICS: Final[tuple[bytes, ...]] = (
    b'\x7fELF',
    b'\xfe\xed\xfa\xce',
    b'\xfe\xed\xfa\xcf',
    b'\xce\xfa\xed\xfe',
    b'\xcf\xfa\xed\xfe',
    b'\xca\xfe\xba\xbe',
)


def relocate(
    source_directory: Path,
    destination_directory: Path,
    *,
    encoding: str = 'utf-8',
) -> None:
    """
    Copy and relocate a Python virtual environment.

    Update the paths in the text files: the scripts in ``bin/`` (shebangs, activate scripts),
    ``*.egg-link``, ``*.pth`` and ``RECORD``. The bytecode is removed, Python compiling it anew on
    import, and symbolic links are left as they are.

    A binary keeps the old path: a compiled file in ``bin/`` (a copied interpreter) or an extension
    module. A wheel's extension modules and a copied interpreter do not depend on it. An extension
    built in the environment with an absolute RPATH does: after a move it fails to import, and after
    a copy it still loads the libraries of the old location, until it is rebuilt.
    """
    if not destination_directory.exists():
        rsync(source_directory, destination_directory, destination_is_dir=True, recursive=True)

    b_source_directory = str(source_directory).encode(encoding)
    b_destination_directory = str(destination_directory).encode(encoding)

    for path in find_recursive(destination_directory, '*.pyc'):
        path.unlink()

    for path in itertools.chain.from_iterable(
        [
            find_recursive(destination_directory, ['*.egg-link', '*.pth', 'RECORD']),
            find_recursive(destination_directory / 'bin', '*'),
        ]
    ):
        if path.is_symlink():
            continue

        with path.open('r+b') as f:
            if _is_binary(head := f.read(BINARY_HEAD_SIZE)):
                continue

            content = (head + f.read()).replace(b_source_directory, b_destination_directory)
            f.seek(0)
            f.write(content)
            f.truncate()


# --- Internals ------------------------------------------------------------------------------------


def _is_binary(head: bytes) -> bool:
    """Return True for the head of a binary: a known magic number, or a NUL byte (a PE, for one)."""
    return head.startswith(BINARY_MAGICS) or b'\x00' in head
