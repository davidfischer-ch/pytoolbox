"""
Module related to file system and path operations.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, BinaryIO, Literal, Protocol, Self, TypeAlias, TextIO, overload
import contextlib
import collections
import copy
import datetime
import errno
import grp
import os
import pwd
import re
import shutil
import tempfile
import time
import uuid

import magic

from . import module
from .datetime import datetime_now
from .decorators import deprecated
from .regex import from_path_patterns

_all = module.All(globals())

FindPatterns: TypeAlias = re.Pattern | str | list[re.Pattern] | list[str] | list[re.Pattern | str]


class CopyProgressCallback(Protocol):  # pylint:disable=too-few-public-methods
    def __call__(
        self,
        start_date: datetime.datetime,
        elapsed_time: float,
        eta_time: float,
        src_size: int,
        dst_size: int,
        ratio: float
    ) -> None:
        ...


class TemplateHookFunc(Protocol):  # pylint:disable=too-few-public-methods
    def __call__(self, content: str, values: dict[str, Any], *, jinja2: bool = False) -> str:
        ...


@contextlib.contextmanager
def chdir(path: Path):
    """Set working directory then restore previous working directory value on exit."""
    here = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(here)


def chown(
    path: Path,
    user: int | str | None = None,
    group: int | str | None = None,
    *,
    recursive: bool = False,
    top_down: bool = True,
    on_error: Callable | None = None,
    follow_symlinks: bool = False
) -> None:
    """
    Change owner/group of a path, can be recursive.
    Both can be a name, an id or None to leave it unchanged.
    """
    uid = to_user_id(user)
    gid = to_group_id(group)
    if recursive:
        # TODO When Python >= 3.12 then path.walk
        for dirpath, _, filenames in os.walk(
            path,
            topdown=top_down,
            onerror=on_error,
            followlinks=follow_symlinks
        ):
            dir_path = Path(dirpath)
            os.chown(dir_path, uid, gid)
            for filename in filenames:
                os.chown(dir_path / filename, uid, gid)
    else:
        os.chown(path, uid, gid)


def copy_recursive(  # pylint:disable=too-many-arguments,too-many-locals
    source_path: Path,
    destination_path: Path,
    patterns: FindPatterns = '*',
    *,
    regex: bool = False,
    top_down: bool = True,
    on_error: Callable | None = None,
    follow_symlinks: bool = False,

    # Processing arguments
    chunk_size: int = 1024 * 1024,
    progress_callback: CopyProgressCallback | None = None,
    ratio_delta: float = 0.01,
    time_delta: float | int = 1,
    check_size: bool = True,
    remove_on_error: bool = True,
) -> dict[str, Any]:
    """
    Copy the content of a source directory to a destination directory.
    This function is based on a block-copy algorithm making progress update possible.

    Given `progress_callback` will be called with *start_date*, *elapsed_time*, *eta_time*,
    *src_size*, *dst_size* and *ratio*. Set `remove_on_error` to remove the destination directory
    in case of error.

    This function will return a dictionary containing *start_date*, *elapsed_time* and *src_size*.
    At the end of the copy, if the size of the destination directory is not equal to the source
    then a `IOError` is raised.
    """
    try:
        start_date = datetime_now()
        start_time = time.time()
        src_size = get_size(
            path=source_path,
            patterns=patterns,
            regex=regex,
            top_down=top_down,
            on_error=on_error,
            follow_symlinks=follow_symlinks)
        dst_size = 0

        # Recursive copy of a directory of files
        for src_path in find_recursive(
            directory=source_path,
            patterns=patterns,
            regex=regex,
            top_down=top_down,
            on_error=on_error,
            follow_symlinks=follow_symlinks
        ):
            dst_path = destination_path / src_path.relative_to(source_path)
            makedirs(dst_path, parent=True)

            # Initialize block-based copy
            src_file = src_path.open('rb')  # pylint: disable=consider-using-with
            dst_file = dst_path.open('wb')  # pylint: disable=consider-using-with

            # Block-based copy loop
            block_pos: int = 0
            prev_ratio: float = 0
            prev_time: float = 0
            while True:
                block = src_file.read(chunk_size)
                try:
                    ratio = float(dst_size) / src_size
                    ratio = 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
                except ZeroDivisionError:
                    ratio = 1.0
                elapsed_time = time.time() - start_time

                # Update status of job only if delta time or delta ratio is sufficient
                if (
                    progress_callback is not None
                    and ratio - prev_ratio > ratio_delta
                    and elapsed_time - prev_time > time_delta
                ):
                    prev_ratio = ratio
                    prev_time = elapsed_time
                    eta_time = int(elapsed_time * (1.0 - ratio) / ratio) if ratio > 0 else 0
                    progress_callback(
                        start_date=start_date,
                        elapsed_time=elapsed_time,
                        eta_time=eta_time,
                        src_size=src_size,
                        dst_size=dst_size,
                        ratio=ratio)

                block_length = len(block)
                block_pos += block_length
                dst_size += block_length

                if not block:
                    break  # End of input reached

                dst_file.write(block)

            # FIXME maybe a finally block for that
            src_file.close()
            dst_file.close()

        # Output directory sanity check
        if check_size:
            if (dst_size := get_size(destination_path)) != src_size:
                raise IOError(f'Destination size does not match source ({src_size} vs {dst_size})')

        elapsed_time = time.time() - start_time
        return {'start_date': start_date, 'elapsed_time': elapsed_time, 'src_size': src_size}
    except Exception:
        if remove_on_error:
            shutil.rmtree(destination_path, ignore_errors=True)
        raise


def find_recursive(
    directory: Path,
    patterns: FindPatterns,
    *,
    regex: bool = False,
    top_down: bool = True,
    on_error: Callable | None = None,
    follow_symlinks: bool = False
) -> Iterator[Path]:
    """
    Yield filenames matching any of the patterns.
    Patterns will be compiled to regular expressions, if necessary.

    If `regex` is set to True, then any string pattern will be converted from the unix-style
    wildcard to the regular expression equivalent using :func:`fnatmch.translate`.

    **Example usage**

    >>> from pathlib import Path
    >>> import re
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> next(find_recursive(directory, '*/collections*')) == directory / 'collections.py'
    True
    >>> filenames = sorted(find_recursive(directory, ['*/django*', '*/*.py']))
    >>> [f.name for f in filenames[-4:]]
    ['unittest.py', 'validation.py', 'virtualenv.py', 'voluptuous.py']
    >>> (directory / 'aws' / 's3.py') in filenames
    True
    >>> (directory / 'django') in filenames  # Its a directory
    False
    >>> a_files = set(find_recursive(directory, re.compile(r'.*/st.+\\.py$')))
    >>> b_files = set(find_recursive(directory, ['.*/st.+\\.py$'], regex=True))
    >>> a_files == b_files
    True
    >>> [f.name for f in sorted(a_files)]
    ['storage.py', 'states.py', 'string.py']
    """
    patterns = from_path_patterns(patterns, regex=regex)
    # TODO When Python >= 3.12 then path.walk
    for dirpath, _, filenames in os.walk(
        directory,
        topdown=top_down,
        onerror=on_error,
        followlinks=follow_symlinks
    ):
        dir_path = Path(dirpath)
        for filename in filenames:
            file_path = dir_path / filename
            if any(p.match(str(file_path)) for p in patterns):
                yield file_path


def file_mime(path: Path, *, mime: bool = True) -> str | None:
    """
    Return file mime type.

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> file_mime(directory / '..' / 'setup.cfg')
    'text/plain'
    >>> file_mime(directory / 'filesystem.py') in ('text/plain', 'text/x-python')
    True
    >>> file_mime('missing-file') is None
    True
    """
    try:
        return magic.from_file(str(path), mime=mime)
    except OSError:
        return None


def first_that_exist(*paths: Path) -> Path | None:
    """
    Returns the first file/directory that exist.

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> assert first_that_exist(Path('foo'), directory) == directory
    >>> assert first_that_exist(Path('does_not_exist.com'), Path('..')) == Path('..')
    >>> assert first_that_exist(Path('does_not_exist.ch')) is None
    """
    try:
        return next(path for path in paths if path.exists())
    except StopIteration:
        return None


def from_template(
    template: Path | str,
    target: Path | None,
    values: dict[str, Any],
    *,
    jinja2: bool = False,
    pre_func: TemplateHookFunc | None = None,
    post_func: TemplateHookFunc | None = None,
    directories: Path | list[Path] = Path('.')
) -> str:
    """
    Return a `template` rendered with `values` using string.format or Jinja2 as the template engine.

    * Optionally set `target` to a path to store the output.
    * Set `{pre,post}_func` to a callback function with the signature f(content, values, jinja2)
    * Set `directories` to the paths where the Jinja2 loader will lookup for *base* templates.

    **Example usage**

    >>> template_path = Path('config.template')
    >>> target_path = Path('config')

    >>> template = '{{username={user}; password={pass}}}'
    >>> values = {'user': 'tabby', 'pass': 'miaow', 'other': 10}
    >>> template_path.write_text(template, encoding='utf-8')
    36

    The behavior when all keys are given (and even more):

    >>> _ = from_template(template_path, Path('config'), values)
    >>> target_path.read_text(encoding='utf-8')
    '{username=tabby; password=miaow}'

    >>> _ = from_template(template, target_path, values)
    >>> Path('config').read_text(encoding='utf-8')
    '{username=tabby; password=miaow}'

    >>> def post_func(content: str, values: dict[str, Any], jinja2: bool) -> str:
    ...     return content.replace('tabby', 'tikky')
    >>> from_template(template, None, values, post_func=post_func)
    '{username=tikky; password=miaow}'

    The behavior if a value for a key is missing:

    >>> from_template(template_path, target_path, {'pass': 'miaow', 'other': 10})
    Traceback (most recent call last):
        ...
    KeyError: ...'user'
    >>> target_path.read_text(encoding='utf-8')
    '{username=tabby; password=miaow}'

    >>> template_path.unlink()
    >>> target_path.unlink()
    """
    content = template.read_text(encoding='utf-8') if isinstance(template, Path) else template
    if pre_func:
        content = pre_func(content, values=values, jinja2=jinja2)
    if jinja2:
        from jinja2 import Environment, FileSystemLoader, StrictUndefined
        loader = FileSystemLoader(directories)
        environment = Environment(loader=loader, undefined=StrictUndefined)
        content = environment.from_string(content).render(**values)
    else:
        content = content.format(**values)
    if post_func:
        content = post_func(content, values=values, jinja2=jinja2)
    if target:
        target.write_text(content, encoding='utf-8')
    return content


def get_bytes(
    data: Path | bytes | str,
    *,
    encoding: str = 'utf-8',
    chunk_size: int | None = None
) -> Iterator[bytes]:
    """
    Yield the content read from the given `path` or the `data` converted to bytes.

    Remark: Value of `encoding` is used only if `data` is actually a string.
    """
    if isinstance(data, Path):
        with data.open('rb') as f:
            if chunk_size is not None:
                while data := f.read(chunk_size):
                    yield data
            else:
                yield f.read()
    else:
        yield data.encode(encoding) if isinstance(data, str) else data


def get_size(
    path: Path,
    patterns: FindPatterns = '*',
    *,
    regex: bool = False,
    top_down: bool = True,
    on_error: Callable | None = None,
    follow_symlinks: bool = False
) -> int:
    """
    Returns the size of a file or directory.

    If given `path` is a directory (or symlink to a directory), then returned value is computed by
    summing the size of all files, and that recursively.

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> directory = Path(__file__).resolve().parent
    >>>
    >>> get_size(directory / '..' / 'LICENSE.rst')
    5747
    >>> get_size(directory / '..', '*.rst') > 1000
    True
    >>> get_size(directory / '..', '.*/v[^/]+\\.py', regex=True) > 10000
    True
    """
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in find_recursive(
        directory=path,
        patterns=patterns,
        regex=regex,
        top_down=top_down,
        on_error=on_error,
        follow_symlinks=follow_symlinks))


def makedirs(path: Path, *, mode: int = 0o777, parent: bool = False) -> bool:
    """
    Recursively make directories (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if directory found and re-raise any other type
    of exception (raised by `os.makedirs`).

    **Example usage**

    >>> import os, shutil
    >>> from pathlib import Path
    >>>
    >>> filesystem_py = Path(__file__).resolve()
    >>>
    >>> makedirs(Path('/etc'))
    False
    >>> makedirs(Path('/tmp/salut/mec'))
    True
    >>> shutil.rmtree('/tmp/salut')
    >>>
    >>> makedirs(Path('/tmp/some/path/file.txt'), parent=True)
    True
    >>> os.path.exists('/tmp/some/path')
    True
    >>> os.path.exists('/tmp/some/path/file.txt')
    False
    >>> shutil.rmtree('/tmp/some')
    >>>
    >>> makedirs(Path(filesystem_py))
    Traceback (most recent call last):
        ...
    FileExistsError: ...
    """
    if parent:
        path = path.parent
    try:
        os.makedirs(path, mode=mode)
        return True
    except OSError as ex:
        # Directory exists
        if ex.errno == errno.EEXIST and path.is_dir():
            return False
        raise  # Re-raise exception if a different error occurred


@deprecated
def recursive_copy(*args, **kwargs):
    return copy_recursive(*args, **kwargs)


def remove(path: Path | str, *, recursive: bool = False):
    """
    Remove a file/directory (which may not exists) without throwing an exception.
    Returns True if operation is successful, False if file/directory not found and re-raise any
    other type of exception.

    **Example usage**

    >>> from pathlib import Path
    >>>
    >>> import pytest
    >>>
    >>> Path('remove.example').write_text('salut les pépés', encoding='utf-8')
    15
    >>> remove('remove.example')
    True
    >>> remove('remove.example')
    False
    >>> for file_name in ('remove/a', 'remove/b/c', 'remove/d/e/f'):
    ...     file_path = Path(file_name)
    ...     _ = makedirs(file_path, parent=True)
    ...     file_path.write_text('salut les pépés', encoding='utf-8')
    15
    15
    15
    >>> remove(Path('remove/d/e'), recursive=True)
    True
    >>> remove(Path('remove/d/e'), recursive=True)
    False
    >>> with pytest.raises(OSError):
    ...     remove(Path('remove/b'))
    >>> remove(Path('remove'), recursive=True)
    True
    """
    try:
        try:
            os.remove(path)
            return True
        except Exception as ex:
            # Is a directory and recursion is allowed
            if recursive and (
                isinstance(ex, OSError)
                and ex.errno == errno.EISDIR  # pylint:disable=no-member
                or PermissionError is not None
                and isinstance(ex, PermissionError)
            ):
                shutil.rmtree(path)
                return True
            raise  # Re-raise exception if a different error occurred
    except OSError as ex:
        # File does not exist
        if ex.errno == errno.ENOENT:
            return False
        raise  # Re-raise exception if a different error occurred


def symlink(source, link_name):
    """
    Symlink a file/directory (which may already exists) without throwing an exception. Returns True
    if operation is successful, False if found & target is `link_name` and re-raise any other type
    of exception.

    **Example usage**

    >>> a = remove('/tmp/does_not_exist')
    >>> a = remove('/tmp/does_not_exist_2')
    >>> a = remove('/tmp/link_etc')
    >>> a = remove(os.path.expanduser('~/broken_link'))

    Creating a symlink named /etc does fail - /etc already exist but does not refer to /home:

    >>> from pytoolbox.unittest import asserts
    >>> asserts.raises(OSError, symlink, '/home', '/etc')

    Symlinking /etc to itself only returns that nothing changed:

    >>> symlink('/etc', '/etc')
    False

    Creating a symlink to an existing file has the following behaviour:

    >>> symlink('/etc', '/tmp/link_etc')
    True
    >>> symlink('/etc', '/tmp/link_etc')
    False
    >>> asserts.raises(OSError, symlink, '/etc/does_not_exist', '/tmp/link_etc')
    >>> asserts.raises(OSError, symlink, '/home', '/tmp/link_etc')

    Creating a symlink to a non existing has the following behaviour:

    >>> symlink('~/does_not_exist', '~/broken_link')
    True
    >>> symlink('~/does_not_exist', '~/broken_link')
    False
    >>> asserts.raises(OSError, symlink, '~/does_not_exist_2', '~/broken_link')
    >>> asserts.raises(OSError, symlink, '/home', '~/broken_link')
    >>> os.remove('/tmp/link_etc')
    >>> os.remove(os.path.expanduser('~/broken_link'))
    """
    try:
        source = os.path.expanduser(source)
        link_name = os.path.expanduser(link_name)
        os.symlink(source, link_name)
        return True
    except OSError as e1:  # pylint:disable=invalid-name
        # File exists
        if e1.errno == errno.EEXIST:
            try:
                if os.path.samefile(source, link_name):
                    return False
            except OSError as e2:  # pylint:disable=invalid-name
                # Handle broken symlink that point to same target
                target = os.path.expanduser(os.readlink(link_name))
                if e2.errno == errno.ENOENT:
                    if target == source:
                        return False
                    raise OSError(errno.EEXIST, 'File exists')  # pylint:disable=raise-missing-from
                raise
        raise  # Re-raise exception if a different error occurred


def to_user_id(user: int | str | None):
    """
    Return user ID.

    **Example usage**

    >>> to_user_id('root')
    0
    >>> to_user_id(0)
    0
    >>> to_user_id(None)
    -1
    """
    if isinstance(user, str):
        return pwd.getpwnam(user).pw_uid
    return -1 if user is None else user


def to_group_id(group):
    """
    Return group ID.

    **Example usage**

    >>> to_group_id('root')
    0
    >>> to_group_id(0)
    0
    >>> to_group_id(None)
    -1
    """
    if isinstance(group, str):
        return grp.getgrnam(group).gr_gid
    return -1 if group is None else group


class TempStorage(object):
    """
    Temporary storage handling made easy.

    **Example usage**

    As a context manager:

    >>> import os
    >>> with TempStorage() as tmp:
    ...     directory = tmp.create_tmp_directory()
    ...     os.path.isdir(directory)
    True
    >>> os.path.isdir(directory)
    False
    """
    def __init__(self, root: Path | None = None) -> None:
        self.root: Path = root or Path(tempfile.gettempdir())
        self._path_to_key: dict[Path, str | None] = {}
        self._paths_by_key = collections.defaultdict(set)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, kind, value, traceback) -> None:
        self.remove_all()

    def create_tmp_directory(
        self,
        name: str = 'tmp-{uuid}',
        *,
        key: str | None = None,
        user: int | str | None = None,
        group: int | str | None = None
    ) -> Path:
        """
        **Example usage**

        >>> import os
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> directory.is_dir()
        True
        >>> tmp.remove_all()
        """
        directory = self.root / name.format(uuid=uuid.uuid4().hex)
        self._path_to_key[directory] = key
        self._paths_by_key[key].add(directory)
        makedirs(directory)
        chown(directory, user, group, recursive=True)
        return directory

    @overload
    def create_tmp_file(  # type: ignore[misc]
        self,
        name: str = ...,
        extension: str | None = ...,
        *,
        encoding: Literal[None],
        key: str | None = ...,
        user: int | str | None = ...,
        group: int | str | None = ...,
        return_file: Literal[True] = True
    ) -> BinaryIO:
        ...

    @overload
    def create_tmp_file(  # type: ignore[misc]
        self,
        name: str = ...,
        extension: str | None = ...,
        *,
        encoding: str = ...,
        key: str | None = ...,
        user: int | str | None = ...,
        group: int | str | None = ...,
        return_file: Literal[True] = True
    ) -> TextIO:
        ...

    @overload
    def create_tmp_file(
        self,
        name: str = ...,
        extension: str | None = ...,
        *,
        encoding: str | None = ...,
        key: str | None = ...,
        user: int | str | None = ...,
        group: int | str | None = ...,
        return_file: bool = ...
    ) -> Path:
        ...

    def create_tmp_file(
        self,
        name='tmp-{uuid}',
        extension=None,
        *,
        encoding='utf-8',
        key=None,
        user=None,
        group=None,
        return_file=True
    ):
        """
        **Example usage**

        >>> from pathlib import Path
        >>> tmp = TempStorage()
        >>> file_path = tmp.create_tmp_file(encoding=None, return_file=False)
        >>> file_path.is_file()
        True
        >>> with tmp.create_tmp_file(extension='txt') as f:
        ...     assert Path(f.name).is_file()
        ...     length = f.write('Je suis une théière')
        ...     filename = f.name
        >>> length
        19
        >>> Path(filename).read_text(encoding='utf-8')
        'Je suis une théière'
        >>> tmp.remove_all()
        """
        mode = 'w' if encoding else 'wb'
        name = name.format(uuid=uuid.uuid4().hex) + (f'.{extension}' if extension else '')
        path = self.root / name
        self._path_to_key[path] = key
        self._paths_by_key[key].add(path)

        with path.open(mode, encoding=encoding):
            pass
        chown(path, user, group)

        if return_file:
            return path.open(mode, encoding=encoding)  # pylint: disable=consider-using-with

        return path

    def remove_by_path(self, path: Path) -> None:
        """
        **Example usage**

        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> tmp.remove_by_path(directory)
        >>> with asserts.raises(KeyError):
        ...     tmp.remove_by_path(directory)
        >>> with asserts.raises(KeyError):
        ...     tmp.remove_by_path(Path('random-path'))
        """
        key = self._path_to_key[path]
        remove(path, recursive=True)
        del self._path_to_key[path]
        self._paths_by_key[key].remove(path)

    def remove_by_key(self, key: str | None = None) -> None:
        """
        **Example usage**

        >>> tmp = TempStorage()
        >>> d1 = tmp.create_tmp_directory()
        >>> d2 = tmp.create_tmp_directory(key=10)
        >>> tmp.remove_by_key(10)
        >>> d1.is_dir()
        True
        >>> d2.is_dir()
        False
        >>> tmp.remove_by_key()
        >>> d1.is_dir()
        False
        """
        paths = self._paths_by_key[key]
        for path in copy.copy(paths):
            remove(path, recursive=True)
            paths.remove(path)
            del self._path_to_key[path]
        del self._paths_by_key[key]

    def remove_all(self) -> None:
        """
        **Example usage**

        >>> with TempStorage() as tmp:
        ...     d1 = tmp.create_tmp_directory()
        ...     d2 = tmp.create_tmp_directory(key=10)
        ...     f1 = tmp.create_tmp_file(return_file=False)
        ...     assert d1.is_dir()
        ...     assert d2.is_dir()
        ...     assert f1.is_file()
        ... # Tip: The context manager calls remove_all
        >>> assert not d1.is_dir()
        >>> assert not d2.is_dir()
        >>> assert not f1.is_file()
        """
        for key in self._paths_by_key.copy().keys():
            self.remove_by_key(key)


__all__ = _all.diff(globals())
