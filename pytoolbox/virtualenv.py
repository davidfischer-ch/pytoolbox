import itertools, os

from .filesystem import find_recursive
from .subprocess import rsync

__all__ = ['relocate']


def relocate(source_directory, destination_directory, encoding='utf-8'):
    """
    Copy and relocate a Python virtual environment.
    Update the paths in `*.egg-link, *.pth, *.pyc`, etc.
    """

    if not os.path.exists(destination_directory):
        rsync(
            source_directory,
            destination_directory,
            destination_is_dir=True,
            makedest=True,
            recursive=True
        )

    b_source_directory = source_directory.encode(encoding)
    b_destination_directory = destination_directory.encode(encoding)

    for path in itertools.chain.from_iterable([
        find_recursive(destination_directory, ['*.egg-link', '*.pth', '*.pyc', 'RECORD']),
        find_recursive(os.path.join(destination_directory, 'bin'), '*'),
        find_recursive(os.path.join(destination_directory, 'src'), '*.so')
    ]):
        with open(path, 'r+b') as f:
            content = f.read().replace(b_source_directory, b_destination_directory)
            f.seek(0)
            f.write(content)
            f.truncate()
