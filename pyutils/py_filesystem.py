#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import errno, grp, pwd, os, shutil, time
from six import string_types
from py_datetime import datetime_now


def first_that_exist(*paths):
    u"""
    Returns the first file/directory that exist.

    **Example usage**:

    >>> print(first_that_exist(u'', u'/etc', u'.'))
    /etc
    >>> print(first_that_exist(u'does_not_exist.com', u'', u'..'))
    ..
    """
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def get_size(path):
    u"""
    Returns the size of a file or directory.
    If given ``path`` is a directory (or symlink to a directory), then returned value is computed by
    summing the size of all files, and that recursively.
    """
    if os.path.isfile(path):
        return os.stat(path).st_size
    size = 0
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            size += os.stat(os.path.join(root, filename)).st_size
    return size


def recursive_copy(source_path, destination_path, callback, ratio_delta=0.01, time_delta=1):
    u"""
    Copy the content of a source directory to a destination directory.
    This method is based on a block-copy algorithm making progress update possible.

    Given ``callback`` would be called with *start_date*, *elapsed_time*, *eta_time*, *src_size*,
    *dst_size* and *ratio*.

    This method will return a dictionary containing *start_date*, *elapsed_time* and *src_size*.
    At the end of the copy, if the size of the destination directory is not equal to the source then
    a ``IOError`` is raised. The destination directory is removed in case of error.
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
                src_file = open(src_path, u'rb')
                dst_file = open(dst_path, u'wb')

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
                    if ratio - prev_ratio > ratio_delta and elapsed_time - prev_time > time_delta:
                        prev_ratio = ratio
                        prev_time = elapsed_time
                        eta_time = int(elapsed_time * (1.0 - ratio) / ratio) if ratio > 0 else 0
                        callback(start_date, elapsed_time, eta_time, src_size, dst_size, ratio)
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
        dst_size = get_size(destination_path)
        if dst_size != src_size:
            raise IOError(
                u'Destination size does not match source ({0} vs {1})'.format(src_size, dst_size))

        elapsed_time = time.time() - start_time
        return {u'start_date': start_date, u'elapsed_time': elapsed_time, u'src_size': src_size}
    except:
        # Cleanup - remove output directory
        shutil.rmtree(destination_path, ignore_errors=True)
        raise


def try_makedirs(path):
    u"""
    Tries to recursive make directories (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if directory found and re-raise any other type of
    exception.

    **Example usage**:

    >>> import shutil
    >>> try_makedirs(u'/etc')
    False
    >>> try_makedirs(u'/tmp/salut/mec')
    True
    >>> shutil.rmtree(u'/tmp/salut/mec')
    """
    try:
        os.makedirs(path)
        return True
    except OSError as e:
        # File exists
        if e.errno == errno.EEXIST:
            return False
        raise  # Re-raise exception if a different error occurred


def try_remove(path):
    u"""
    Tries to remove a file/directory (which may not exists) without throwing an exception.
    Returns True if operation is successful, False if file/directory not found and re-raise any
    other type of exception.

    **Example usage**:

    >>> open(u'try_remove.example', u'w').write(u'salut')
    >>> try_remove(u'try_remove.example')
    True
    >>> try_remove(u'try_remove.example')
    False
    """
    try:
        os.remove(path)
        return True
    except OSError as e:
        # File does not exist
        if e.errno == errno.ENOENT:
            return False
        raise  # Re-raise exception if a different error occurred


def try_symlink(source, link_name):
    u"""
    Tries to symlink a file/directory (which may already exists) without throwing an exception.
    Returns True if operation is successful, False if found & target is ``link_name`` and re-raise
    any other type of exception.

    **Example usage**:

    >>> a = try_remove(u'/tmp/does_not_exist')
    >>> a = try_remove(u'/tmp/does_not_exist_2')
    >>> a = try_remove(u'/tmp/link_etc')
    >>> a = try_remove(os.path.expanduser(u'~/broken_link'))

    Creating a symlink named /etc does fail - /etc already exist but does not refer to /home:

    >>> import shutil
    >>> try_symlink(u'/home', u'/etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    Symlinking /etc to itself only returns that nothing changed:

    >>> try_symlink(u'/etc', u'/etc')
    False

    Creating a symlink to an existing file has the following behaviour:

    >>> try_symlink(u'/etc', u'/tmp/link_etc')
    True
    >>> try_symlink(u'/etc', u'/tmp/link_etc')
    False
    >>> try_symlink(u'/etc/does_not_exist', u'/tmp/link_etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists
    >>> try_symlink(u'/home', u'/tmp/link_etc')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    Creating a symlink to a non existing has the following behaviour:

    >>> try_symlink(u'~/does_not_exist', u'~/broken_link')
    True
    >>> try_symlink(u'~/does_not_exist', u'~/broken_link')
    False
    >>> try_symlink(u'~/does_not_exist_2', u'~/broken_link')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists
    >>> try_symlink(u'/home', u'~/broken_link')
    Traceback (most recent call last):
        ...
    OSError: [Errno 17] File exists

    >>> os.remove(u'/tmp/link_etc')
    >>> os.remove(os.path.expanduser(u'~/broken_link'))
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
                        raise OSError(errno.EEXIST, u'File exists')
                raise
        raise  # Re-raise exception if a different error occurred


def chown(path, user, group, recursive=False):
    u"""
    Change owner/group of a path, can be recursive. User and group can be a name or an id.
    """
    uid = pwd.getpwnam(user).pw_uid if isinstance(user, string_types) else user
    gid = grp.getgrnam(group).gr_gid if isinstance(group, string_types) else group
    if recursive:
        for root, dirnames, filenames in os.walk(path):
            os.chown(root, uid, gid)
            for filename in filenames:
                os.chown(os.path.join(root, filename), uid, gid)
    else:
        os.chown(path, uid, gid)
