from __future__ import annotations

from pathlib import Path
import itertools

from .filesystem import find_recursive
from .subprocess import rsync

__all__ = ['relocate']


def relocate(
    source_directory: Path,
    destination_directory: Path,
    *,
    encoding: str = 'utf-8'
) -> None:
    """
    Copy and relocate a Python virtual environment.
    Update the paths in `*.egg-link, *.pth, *.pyc`, etc.
    """
    if not destination_directory.exists():
        rsync(source_directory, destination_directory, destination_is_dir=True, recursive=True)

    b_source_directory = str(source_directory).encode(encoding)
    b_destination_directory = str(destination_directory).encode(encoding)

    for path in itertools.chain.from_iterable([
        find_recursive(destination_directory, ['*.egg-link', '*.pth', '*.pyc', 'RECORD']),
        find_recursive(destination_directory / 'bin', '*'),
        find_recursive(destination_directory / 'src', '*.so')
    ]):
        with path.open('r+b') as f:
            content = f.read().replace(b_source_directory, b_destination_directory)
            f.seek(0)
            f.write(content)
            f.truncate()
