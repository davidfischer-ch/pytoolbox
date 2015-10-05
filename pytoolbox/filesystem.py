# -*- encoding: utf-8 -*-

"""
Module related to file system and path operations.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, copy, errno, fnmatch, grp, pwd, os, re, shutil, tempfile, time, uuid
from codecs import open

import magic

from . import module
from .datetime import datetime_now
from .encoding import string_types

_all = module.All(globals())


def find_recursive(directory, patterns, unix_wildcards=True, **kwargs):
    """
    Yield filenames matching any of the patterns. Patterns will be compiled to regular expressions, if necessary.

    If `unix_wildcards` is set to True, then any string pattern will be converted from the unix-style wildcard to the
    regular expression equivalent using :func:`fnatmch.translate`.

    **Example usage**

    >>> print(next(find_recursive('/etc', 'interfaces')))
    /etc/network/interfaces
    >>> filenames = list(find_recursive('/etc/network', ['interfaces', 'inter*aces', '*.jpg']))
    >>> filenames.count('/etc/network/interfaces')
    1

    >>> a = set(find_recursive('/etc/network', re.compile('inter?aces')))
    >>> b = set(find_recursive('/etc/network', ['inter?aces'], unix_wildcards=False))
    >>> a == b
    True
    """
    if isinstance(patterns, string_types) or hasattr(patterns, 'match'):
        patterns = [patterns]
    patterns = [
        p if hasattr(p, 'match') else re.compile(fnmatch.translate(p) if unix_wildcards else p) for p in patterns
    ]
    for dirpath, dirnames, filenames in os.walk(directory, **kwargs):
        for filename in filenames:
            if any(p.match(filename) for p in patterns):
                yield os.path.join(dirpath, filename)


def file_mime(path, mime=True):
    try:
        return magic.from_file(path, mime=mime).decode('utf-8')
    except OSError:
        return None


def first_that_exist(*paths):
    """
    Returns the first file/directory that exist.

    **Example usage**

    >>> print(first_that_exist('', '/etc', '.'))
    /etc
    >>> print(first_that_exist('does_not_exist.com', '', '..'))
    ..
    >>> print(first_that_exist('does_not_exist.ch'))
    None
    """
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def from_template(template, destination, values, jinja2=False):
    """
    Generate a `destination` file from a `template` file filled with `values`, method: string.format or jinja2!

    **Example usage**

    >>> open('config.template', 'w', 'utf-8').write('{{username={user}; password={pass}}}')

    The behavior when all keys are given (and even more):

    >>> from_template('config.template', 'config', {'user': 'tabby', 'pass': 'miaow', 'other': 10})
    >>> print(open('config', 'r', 'utf-8').read())
    {username=tabby; password=miaow}

    The behavior if a value for a key is missing:

    >>> from_template('config.template', 'config', {'pass': 'miaow', 'other': 10})  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    KeyError: ...'user'
    >>> print(open('config', 'r', 'utf-8').read())
    <BLANKLINE>

    >>> os.remove('config.template')
    >>> os.remove('config')
    """
    with open(template, 'r', 'utf-8') as template_file:
        with open(destination, 'w', 'utf-8') as destination_file:
            content = template_file.read()
            if jinja2:
                from jinja2 import Template
                content = Template(content).render(**values)
            else:
                content = content.format(**values)
            destination_file.write(content)


def get_bytes(path_or_data, encoding='utf-8', is_path=False, chunk_size=None):
    """
    Yield the content read from the given `path` or the `data` converted to bytes.

    Remark: Value of `encoding` is used only if `data` is actually a string.
    """
    if is_path:
        with open(path_or_data, 'rb') as f:
            if chunk_size is not None:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
            else:
                yield f.read()
    else:
        yield path_or_data.encode(encoding) if isinstance(path_or_data, string_types) else path_or_data


def get_size(path):
    """
    Returns the size of a file or directory.

    If given `path` is a directory (or symlink to a directory), then returned value is computed by summing the size of
    all files, and that recursively.
    """
    if os.path.isfile(path):
        return os.stat(path).st_size
    size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            size += os.stat(os.path.join(dirpath, filename)).st_size
    return size


def recursive_copy(source_path, destination_path, progress_callback=None, ratio_delta=0.01, time_delta=1,
                   check_size=True, remove_on_error=True):
    """
    Copy the content of a source directory to a destination directory.
    This function is based on a block-copy algorithm making progress update possible.

    Given `progress_callback` will be called with *start_date*, *elapsed_time*, *eta_time*, *src_size*, *dst_size* and
    *ratio*. Set `remove_on_error` to remove the destination directory in case of error.

    This function will return a dictionary containing *start_date*, *elapsed_time* and *src_size*.
    At the end of the copy, if the size of the destination directory is not equal to the source then a `IOError` is
    raised.
    """
    try:
        start_date, start_time = datetime_now(), time.time()
        src_size, dst_size = get_size(source_path), 0

        # Recursive copy of a directory of files
        for src_root, dirnames, filenames in os.walk(source_path):
            for filename in filenames:
                dst_root = src_root.replace(source_path, destination_path)
                src_path = os.path.join(src_root, filename)
                dst_path = os.path.join(dst_root, filename)

                # Initialize block-based copy
                try_makedirs(os.path.dirname(dst_path))
                block_size = 1024 * 1024
                src_file = open(src_path, 'rb')
                dst_file = open(dst_path, 'wb')

                # Block-based copy loop
                block_pos = prev_ratio = prev_time = 0
                while True:
                    block = src_file.read(block_size)
                    try:
                        ratio = float(dst_size) / src_size
                        ratio = 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
                    except ZeroDivisionError:
                        ratio = 1.0
                    elapsed_time = time.time() - start_time
                    # Update status of job only if delta time or delta ratio is sufficient
                    if progress_callback is not None and \
                            ratio - prev_ratio > ratio_delta and elapsed_time - prev_time > time_delta:
                        prev_ratio = ratio
                        prev_time = elapsed_time
                        eta_time = int(elapsed_time * (1.0 - ratio) / ratio) if ratio > 0 else 0
                        progress_callback(start_date, elapsed_time, eta_time, src_size, dst_size, ratio)
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
            dst_size = get_size(destination_path)
            if dst_size != src_size:
                raise IOError('Destination size does not match source ({0} vs {1})'.format(src_size, dst_size))

        elapsed_time = time.time() - start_time
        return {'start_date': start_date, 'elapsed_time': elapsed_time, 'src_size': src_size}
    except:
        if remove_on_error:
            shutil.rmtree(destination_path, ignore_errors=True)
        raise


def try_makedirs(path):
    """
    Tries to recursive make directories (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if directory found and re-raise any other type of exception.

    **Example usage**

    >>> import shutil
    >>> try_makedirs('/etc')
    False
    >>> try_makedirs('/tmp/salut/mec')
    True
    >>> shutil.rmtree('/tmp/salut/mec')
    """
    try:
        os.makedirs(path)
        return True
    except OSError as e:
        # File exists
        if e.errno == errno.EEXIST:
            return False
        raise  # Re-raise exception if a different error occurred


def try_remove(path, recursive=False):
    """
    Tries to remove a file/directory (which may not exists) without throwing an exception.
    Returns True if operation is successful, False if file/directory not found and re-raise any other type of exception.

    **Example usage**

    >>> open('try_remove.example', 'w', encoding='utf-8').write('salut les pépés')
    >>> try_remove('try_remove.example')
    True
    >>> try_remove('try_remove.example')
    False

    >>> for file_name in ('try_remove/a', 'try_remove/b/c', 'try_remove/d/e/f'):
    ...     _ = try_makedirs(os.path.dirname(file_name))
    ...     open(file_name, 'w', encoding='utf-8').write('salut les pépés')
    >>> try_remove('try_remove/d/e', recursive=True)
    True
    >>> try_remove('try_remove/d/e', recursive=True)
    False
    >>> from nose.tools import assert_raises
    >>> assert_raises(OSError, try_remove, 'try_remove/b')
    >>> try_remove('try_remove', recursive=True)
    True
    """
    try:
        try:
            os.remove(path)
            return True
        except OSError as e:
            # Is a directory and recursion is allowed
            if e.errno == errno.EISDIR and recursive:
                shutil.rmtree(path)
                return True
            raise  # Re-raise exception if a different error occurred
    except OSError as e:
        # File does not exist
        if e.errno == errno.ENOENT:
            return False
        raise  # Re-raise exception if a different error occurred


def try_symlink(source, link_name):
    """
    Tries to symlink a file/directory (which may already exists) without throwing an exception. Returns True if
    operation is successful, False if found & target is `link_name` and re-raise any other type of exception.

    **Example usage**

    >>> a = try_remove('/tmp/does_not_exist')
    >>> a = try_remove('/tmp/does_not_exist_2')
    >>> a = try_remove('/tmp/link_etc')
    >>> a = try_remove(os.path.expanduser('~/broken_link'))

    Creating a symlink named /etc does fail - /etc already exist but does not refer to /home:

    >>> from nose.tools import assert_raises
    >>> assert_raises(OSError, try_symlink, '/home', '/etc')

    Symlinking /etc to itself only returns that nothing changed:

    >>> try_symlink('/etc', '/etc')
    False

    Creating a symlink to an existing file has the following behaviour:

    >>> try_symlink('/etc', '/tmp/link_etc')
    True
    >>> try_symlink('/etc', '/tmp/link_etc')
    False
    >>> assert_raises(OSError, try_symlink, '/etc/does_not_exist', '/tmp/link_etc')
    >>> assert_raises(OSError, try_symlink, '/home', '/tmp/link_etc')

    Creating a symlink to a non existing has the following behaviour:

    >>> try_symlink('~/does_not_exist', '~/broken_link')
    True
    >>> try_symlink('~/does_not_exist', '~/broken_link')
    False
    >>> assert_raises(OSError, try_symlink, '~/does_not_exist_2', '~/broken_link')
    >>> assert_raises(OSError, try_symlink, '/home', '~/broken_link')
    >>> os.remove('/tmp/link_etc')
    >>> os.remove(os.path.expanduser('~/broken_link'))
    """
    try:
        source = os.path.expanduser(source)
        link_name = os.path.expanduser(link_name)
        os.symlink(source, link_name)
        return True
    except OSError as e1:
        # File exists
        if e1.errno == errno.EEXIST:
            try:
                if os.path.samefile(source, link_name):
                    return False
            except OSError as e2:
                # Handle broken symlink that point to same target
                target = os.path.expanduser(os.readlink(link_name))
                if e2.errno == errno.ENOENT:
                    if target == source:
                        return False
                    else:
                        raise OSError(errno.EEXIST, 'File exists')
                raise
        raise  # Re-raise exception if a different error occurred


def chown(path, user=None, group=None, recursive=False):
    """Change owner/group of a path, can be recursive. Both can be a name, an id or None to leave it unchanged."""
    uid = pwd.getpwnam(user).pw_uid if isinstance(user, string_types) else (-1 if user is None else user)
    gid = grp.getgrnam(group).gr_gid if isinstance(group, string_types) else (-1 if group is None else group)
    if recursive:
        for dirpath, dirnames, filenames in os.walk(path):
            os.chown(dirpath, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(dirpath, filename), uid, gid)
    else:
        os.chown(path, uid, gid)


class TempStorage(object):
    """
    Temporary storage handling made easy.

    **Example usage**

    As a context manager:

    >>> import os
    >>> from nose.tools import eq_
    >>> with TempStorage() as tmp:
    ...     directory = tmp.create_tmp_directory()
    ...     eq_(os.path.isdir(directory), True)
    >>> eq_(os.path.isdir(directory), False)
    """
    def __init__(self, root=None):
        self.root = root or tempfile.gettempdir()
        self._path_to_key = {}
        self._paths_by_key = collections.defaultdict(set)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.remove_all()

    def create_tmp_directory(self, path='tmp-{uuid}', key=None, user=None, group=None):
        """
        **Example usage**

        >>> import os
        >>> from nose.tools import eq_
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> eq_(os.path.isdir(directory), True)
        >>> tmp.remove_all()
        """
        directory = os.path.join(self.root, path.format(uuid=uuid.uuid4().hex))
        self._path_to_key[directory] = key
        self._paths_by_key[key].add(directory)
        try_makedirs(directory)
        chown(directory, user, group, recursive=True)
        return directory

    def create_tmp_file(self, path='tmp-{uuid}', extension=None, encoding='utf-8', key=None, user=None, group=None,
                        return_file=True):
        """
        **Example usage**

        >>> import os
        >>> from nose.tools import eq_
        >>> tmp = TempStorage()
        >>> path = tmp.create_tmp_file(encoding=None, return_file=False)
        >>> eq_(os.path.isfile(path), True)
        >>> with tmp.create_tmp_file(extension='txt') as f:
        ...     eq_(os.path.isfile(f.name), True)
        ...     f.write('Je suis une théière')
        ...     path = f.name
        >>> eq_(open(path, encoding='utf-8').read(), 'Je suis une théière')
        >>> tmp.remove_all()
        """
        mode = 'w' if encoding else 'wb'
        path = os.path.join(self.root, path.format(uuid=uuid.uuid4().hex) + ('.%s' % extension if extension else ''))
        self._path_to_key[path] = key
        self._paths_by_key[key].add(path)
        with open(path, mode, encoding=encoding):
            pass
        chown(path, user, group)
        return open(path, mode, encoding=encoding) if return_file else path

    def remove_by_path(self, path):
        """
        **Example usage**

        >>> from nose.tools import assert_raises
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> tmp.remove_by_path(directory)
        >>> with assert_raises(KeyError):
        ...     tmp.remove_by_path(directory)
        >>> with assert_raises(KeyError):
        ...     tmp.remove_by_path('random-path')
        """
        key = self._path_to_key[path]
        try_remove(path, recursive=True)
        del self._path_to_key[path]
        self._paths_by_key[key].remove(path)

    def remove_by_key(self, key=None):
        """
        **Example usage**

        >>> import os
        >>> from nose.tools import eq_
        >>> tmp = TempStorage()
        >>> d1 = tmp.create_tmp_directory()
        >>> d2 = tmp.create_tmp_directory(key=10)
        >>> tmp.remove_by_key(10)
        >>> eq_(os.path.isdir(d1), True)
        >>> eq_(os.path.isdir(d2), False)
        >>> tmp.remove_by_key()
        >>> eq_(os.path.isdir(d1), False)
        """
        paths = self._paths_by_key[key]
        for path in copy.copy(paths):
            try_remove(path, recursive=True)
            paths.remove(path)
            del self._path_to_key[path]
        del self._paths_by_key[key]

    def remove_all(self):
        """
        **Example usage**

        >>> import os
        >>> from nose.tools import eq_
        >>> tmp = TempStorage()
        >>> d1 = tmp.create_tmp_directory()
        >>> d2 = tmp.create_tmp_directory(key=10)
        >>> tmp.remove_all()
        >>> eq_(os.path.isdir(d1), False)
        >>> eq_(os.path.isdir(d2), False)
        >>> tmp.remove_all()
        """
        for key in self._paths_by_key.copy().iterkeys():
            self.remove_by_key(key)

__all__ = _all.diff(globals())
