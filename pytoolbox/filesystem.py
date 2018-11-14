# -*- encoding: utf-8 -*-

"""
Module related to file system and path operations.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, copy, errno, grp, pwd, os, shutil, tempfile, time, uuid
from codecs import open  # pylint:disable=redefined-builtin

import magic

from . import module
from .datetime import datetime_now
from .encoding import string_types
from .regex import from_path_patterns

_all = module.All(globals())


def chown(path, user=None, group=None, recursive=False, **walk_kwargs):
    """
    Change owner/group of a path, can be recursive. Both can be a name, an id or None to leave it
    unchanged.
    """
    uid = to_user_id(user)
    gid = to_group_id(group)
    if recursive:
        for dirpath, dirnames, filenames in os.walk(path, **walk_kwargs):
            os.chown(dirpath, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(dirpath, filename), uid, gid)
    else:
        os.chown(path, uid, gid)


def find_recursive(directory, patterns, unix_wildcards=True, **walk_kwargs):
    """
    Yield filenames matching any of the patterns. Patterns will be compiled to regular expressions,
    if necessary.

    If `unix_wildcards` is set to True, then any string pattern will be converted from
    the unix-style wildcard to the regular expression equivalent using :func:`fnatmch.translate`.

    **Example usage**

    >>> import re
    >>> print(next(find_recursive('/etc', '*/interfaces*')))
    /etc/network/interfaces
    >>> filenames = list(find_recursive('/etc/network', ['*/interfaces*', '*/*.jpg']))
    >>> '/etc/network/interfaces' in filenames
    True
    >>> '/etc/network/interfaces.d' in filenames  # Its a directory
    False
    >>> a = set(find_recursive('/etc', re.compile('.*/host.*')))
    >>> b = set(find_recursive('/etc', ['.*/host.*'], unix_wildcards=False))
    >>> len(a) > 0
    True
    >>> a == b
    True
    """
    patterns = from_path_patterns(patterns, unix_wildcards=unix_wildcards)
    for dirpath, dirnames, filenames in os.walk(directory, **walk_kwargs):
        for filename in filenames:
            filename = os.path.join(dirpath, filename)
            if any(p.match(filename) for p in patterns):
                yield filename


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


def from_template(template, destination, values, is_file=True, jinja2=False, pre_func=None,
                  post_func=None):
    """
    Return a `template` rendered with `values` using string.format or jinja2 as the template engine.

    * Set `destination` to a filename to store the output, to a Falsy value to skip this feature.
    * Set `is_file` to False to use value of `template` as the content and not a filename to read.
    * Set `{pre,post}_func` to a callback function with the signature f(content, values, jinja2)

    **Example usage**

    >>> template = '{{username={user}; password={pass}}}'
    >>> values = {'user': 'tabby', 'pass': 'miaow', 'other': 10}
    >>> open('config.template', 'w', 'utf-8').write(template)

    The behavior when all keys are given (and even more):

    >>> _ = from_template('config.template', 'config', values)
    >>> print(open('config', 'r', 'utf-8').read())
    {username=tabby; password=miaow}

    >>> _ = from_template(template, 'config', values, is_file=False)
    >>> print(open('config', 'r', 'utf-8').read())
    {username=tabby; password=miaow}

    >>> def post_func(content, values, jinja2):
    ...     return content.replace('tabby', 'tikky')
    >>> print(from_template(template, None, values, is_file=False, post_func=post_func))
    {username=tikky; password=miaow}

    The behavior if a value for a key is missing:

    >>> from_template('config.template', 'config', {'pass': 'miaow', 'other': 10})  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    KeyError: ...'user'
    >>> print(open('config', 'r', 'utf-8').read())
    {username=tabby; password=miaow}

    >>> os.remove('config.template')
    >>> os.remove('config')
    """
    content = open(template, 'r', 'utf-8').read() if is_file else template
    if pre_func:
        content = pre_func(content, values=values, jinja2=jinja2)
    if jinja2:
        from jinja2 import Template
        content = Template(content).render(**values)
    else:
        content = content.format(**values)
    if post_func:
        content = post_func(content, values=values, jinja2=jinja2)
    if destination:
        with open(destination, 'w', 'utf-8') as f:
            f.write(content)
    return content


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


def get_size(path, **walk_kwargs):
    """
    Returns the size of a file or directory.

    If given `path` is a directory (or symlink to a directory), then returned value is computed by summing the size of
    all files, and that recursively.
    """
    if os.path.isfile(path):
        return os.stat(path).st_size
    size = 0
    for dirpath, dirnames, filenames in os.walk(path, **walk_kwargs):
        for filename in filenames:
            size += os.stat(os.path.join(dirpath, filename)).st_size
    return size


def makedirs(path, parent=False):
    """
    Recursively make directories (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if directory found and re-raise any other type of exception.

    **Example usage**

    >>> import shutil
    >>> makedirs('/etc')
    False
    >>> makedirs('/tmp/salut/mec')
    True
    >>> shutil.rmtree('/tmp/salut/mec')
    """
    if parent:
        path = os.path.dirname(path)
    try:
        os.makedirs(path)
        return True
    except OSError as e:
        # File exists
        if e.errno == errno.EEXIST:
            return False
        raise  # Re-raise exception if a different error occurred
try_makedirs = makedirs


def recursive_copy(source_path, destination_path, progress_callback=None, ratio_delta=0.01,
                   time_delta=1, check_size=True, remove_on_error=True):
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
                makedirs(os.path.dirname(dst_path))
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
                raise IOError(
                    'Destination size does not match source ({0} vs {1})'
                    .format(src_size, dst_size))

        elapsed_time = time.time() - start_time
        return {'start_date': start_date, 'elapsed_time': elapsed_time, 'src_size': src_size}
    except:
        if remove_on_error:
            shutil.rmtree(destination_path, ignore_errors=True)
        raise


def remove(path, recursive=False):
    """
    Remove a file/directory (which may not exists) without throwing an exception.
    Returns True if operation is successful, False if file/directory not found and re-raise any other type of exception.

    **Example usage**

    >>> open('remove.example', 'w', encoding='utf-8').write('salut les pépés')
    >>> remove('remove.example')
    True
    >>> remove('remove.example')
    False

    >>> for file_name in ('remove/a', 'remove/b/c', 'remove/d/e/f'):
    ...     _ = makedirs(os.path.dirname(file_name))
    ...     open(file_name, 'w', encoding='utf-8').write('salut les pépés')
    >>> remove('remove/d/e', recursive=True)
    True
    >>> remove('remove/d/e', recursive=True)
    False
    >>> from pytoolbox.unittest import asserts
    >>> asserts.raises(OSError, remove, 'remove/b')
    >>> remove('remove', recursive=True)
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
try_remove = remove


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
try_symlink = symlink


def to_user_id(user):
    if isinstance(user, string_types):
        return pwd.getpwnam(user).pw_uid
    return -1 if user is None else user


def to_group_id(group):
    if isinstance(group, string_types):
        return grp.getgrnam(group).gr_gid
    return -1 if group is None else group


class TempStorage(object):
    """
    Temporary storage handling made easy.

    **Example usage**

    As a context manager:

    >>> import os
    >>> from pytoolbox.unittest import asserts
    >>> with TempStorage() as tmp:
    ...     directory = tmp.create_tmp_directory()
    ...     asserts.true(os.path.isdir(directory))
    >>> asserts.false(os.path.isdir(directory))
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
        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> asserts.true(os.path.isdir(directory))
        >>> tmp.remove_all()
        """
        directory = os.path.join(self.root, path.format(uuid=uuid.uuid4().hex))
        self._path_to_key[directory] = key
        self._paths_by_key[key].add(directory)
        makedirs(directory)
        chown(directory, user, group, recursive=True)
        return directory

    def create_tmp_file(self, path='tmp-{uuid}', extension=None, encoding='utf-8', key=None,
                        user=None, group=None, return_file=True):
        """
        **Example usage**

        >>> import os
        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> path = tmp.create_tmp_file(encoding=None, return_file=False)
        >>> asserts.true(os.path.isfile(path))
        >>> with tmp.create_tmp_file(extension='txt') as f:
        ...     asserts.true(os.path.isfile(f.name))
        ...     f.write('Je suis une théière')
        ...     path = f.name
        >>> asserts.equal(open(path, encoding='utf-8').read(), 'Je suis une théière')
        >>> tmp.remove_all()
        """
        mode = 'w' if encoding else 'wb'
        path = os.path.join(
            self.root,
            path.format(uuid=uuid.uuid4().hex) + ('.%s' % extension if extension else ''))
        self._path_to_key[path] = key
        self._paths_by_key[key].add(path)
        with open(path, mode, encoding=encoding):
            pass
        chown(path, user, group)
        return open(path, mode, encoding=encoding) if return_file else path

    def remove_by_path(self, path):
        """
        **Example usage**

        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> directory = tmp.create_tmp_directory()
        >>> tmp.remove_by_path(directory)
        >>> with asserts.raises(KeyError):
        ...     tmp.remove_by_path(directory)
        >>> with asserts.raises(KeyError):
        ...     tmp.remove_by_path('random-path')
        """
        key = self._path_to_key[path]
        remove(path, recursive=True)
        del self._path_to_key[path]
        self._paths_by_key[key].remove(path)

    def remove_by_key(self, key=None):
        """
        **Example usage**

        >>> import os
        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> d1 = tmp.create_tmp_directory()
        >>> d2 = tmp.create_tmp_directory(key=10)
        >>> tmp.remove_by_key(10)
        >>> asserts.true(os.path.isdir(d1))
        >>> asserts.false(os.path.isdir(d2))
        >>> tmp.remove_by_key()
        >>> asserts.false(os.path.isdir(d1))
        """
        paths = self._paths_by_key[key]
        for path in copy.copy(paths):
            remove(path, recursive=True)
            paths.remove(path)
            del self._path_to_key[path]
        del self._paths_by_key[key]

    def remove_all(self):
        """
        **Example usage**

        >>> import os
        >>> from pytoolbox.unittest import asserts
        >>> tmp = TempStorage()
        >>> d1 = tmp.create_tmp_directory()
        >>> d2 = tmp.create_tmp_directory(key=10)
        >>> tmp.remove_all()
        >>> asserts.false(os.path.isdir(d1))
        >>> asserts.false(os.path.isdir(d2))
        >>> tmp.remove_all()
        """
        for key in self._paths_by_key.copy().iterkeys():
            self.remove_by_key(key)


__all__ = _all.diff(globals())
