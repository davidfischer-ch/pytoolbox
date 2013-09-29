# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#  Description    : Toolbox for Python scripts
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pyutils Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pyutils.git

import errno, fcntl, multiprocessing, os, re, setuptools.archive_util, shlex, shutil, subprocess
from .py_filesystem import try_makedirs
from .py_unicode import to_bytes

EMPTY_CMD_RETURN = {u'process': None, u'stdout': None, u'stderr': None, u'returncode': None}


def cmd(command, input=None, cli_input=None, fail=True, log=None, communicate=True, **kwargs):
    u"""
    Calls the ``command`` and returns a dictionary with process, stdout, stderr, and the returncode.

    Returned stdout and stderr will be None if ``communicate`` is set to False.

    * Pipe some content to the command with ``input``.
    * Answer to interactive CLI questions with ``cli_input``.
    * Set ``fail`` to False to avoid the exception ``subprocess.CalledProcessError``.
    * Set ``log`` to a method to log / print details about what is executed / any failure.
    * Set ``communicate`` to True to communicate with the process, this is a locking call.
    * Set kwargs with any argument of the :mod:`subprocess`.Popen constructor excepting stdin, stdout and stderr.
    """
    if hasattr(log, u'__call__'):
        log(u'Execute {0}{1}{2}'.format(u'' if input is None else u'echo {0}|'.format(repr(input)),
            command, u'' if cli_input is None else u' < {0}'.format(repr(cli_input))))
    args = [to_bytes(arg) for arg in command if arg] if isinstance(command, list) else shlex.split(to_bytes(command))
    try:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, **kwargs)
    except OSError as e:
        if fail:
            raise
        return {u'process': None, u'stdout': u'', u'stderr': e, u'returncode': 2}
    if cli_input is not None:
        process.stdin.write(to_bytes(cli_input))
    if communicate:
        stdout, stderr = process.communicate(input=input)
        result = {u'process': process, u'stdout': stdout, u'stderr': stderr, u'returncode': process.returncode}
        if fail and process.returncode != 0:
            if hasattr(log, u'__call__'):
                log(result)
            raise subprocess.CalledProcessError(process.returncode, command, stderr)
        return result
    process.poll()  # To get a returncode that may be None of course ...
    return  {u'process': process, u'stdout': None, u'stderr': None, u'returncode': process.returncode}


# http://stackoverflow.com/a/7730201/190597
def make_async(fd):
    u'''
    Add the O_NONBLOCK flag to a file descriptor.
    '''
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# http://stackoverflow.com/a/7730201/190597
def read_async(fd):
    u'''
    Read some data from a file descriptor, ignoring EAGAIN errors.
    '''
    try:
        return fd.read()
    except IOError as e:
        if e.errno == errno.EAGAIN:
            return u''
        raise

# --------------------------------------------------------------------------------------------------

def make(archive, with_cmake=False, configure_options=u'', make_options=u'-j{0}'.format(multiprocessing.cpu_count()),
         install=True, remove_temporary=True, fail=True, log=None, **kwargs):
    results = {}
    here = os.getcwd()
    path = archive.split(u'.')[0]
    shutil.rmtree(path, ignore_errors=True)
    setuptools.archive_util.unpack_archive(archive, path)
    os.chdir(path)
    if with_cmake:
        try_makedirs(u'build')
        os.chdir(u'build')
        results[u'cmake'] = cmd(u'cmake -DCMAKE_BUILD_TYPE=RELEASE ..', fail=fail, log=log, **kwargs)
    else:
        results[u'configure'] = cmd(u'./configure {0}'.format(configure_options), fail=fail, log=log, **kwargs)
    results[u'make'] = cmd(u'make {0}'.format(make_options), fail=fail, log=log, **kwargs)
    if install:
        results[u'make install'] = cmd(u'make install', fail=fail, log=log, **kwargs)
    os.chdir(here)
    if remove_temporary:
        shutil.rmtree(path)
    return results

# --------------------------------------------------------------------------------------------------

def rsync(source, destination, makedest=False, archive=True, delete=False, exclude_vcs=False,
          progress=False, recursive=False, simulate=False, excludes=None, includes=None,
          rsync_path=None, extra=None, fail=True, log=None, **kwargs):
    if makedest and not os.path.exists(destination):
        os.makedirs(destination)
    source = os.path.normpath(source) + (os.sep if os.path.isdir(source) else u'')
    destination = os.path.normpath(destination) + (os.sep if os.path.isdir(destination) else u'')
    command = [u'rsync',
               u'-a' if archive else None,
               u'--delete' if delete else None,
               u'--progress' if progress else None,
               u'-r' if recursive else None,
               u'--dry-run' if simulate else None]
    if rsync_path is not None:
        command += [u'--rsync-path', rsync_path]
    if extra is not None:
        command += [u'-e', extra]
    if excludes is not None:
        command += [u'--exclude={0}'.format(e) for e in excludes]
    if includes is not None:
        command += [u'--include={0}'.format(i) for i in includes]
    if exclude_vcs:
        command += [u'--exclude=.svn', u'--exclude=.git']
    command += [source, destination]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)


def screen_kill(name=None, fail=True, log=None, **kwargs):
    u"""
    Kill all screen instances called ``name`` or all if ``name`` is None.
    """
    for name in screen_list(name=name, log=log):
        cmd([u'screen', u'-S', name, u'-X', u'quit'], fail=fail, log=log, **kwargs)


def screen_launch(name, command, fail=True, log=None, **kwargs):
    u"""
    Launch a new named screen instance.
    """
    return cmd([u'screen', u'-dmS', name] + (command if isinstance(command, list) else [command]),
               fail=fail, log=log, **kwargs)


def screen_list(name=None, log=None, **kwargs):
    u"""
    Returns a list containing all instances of screen. Can be filtered by ``name``.
    """
    return re.findall(r'\s+(\d+.\S+)\s+\(.*\).*',
                      unicode(cmd([u'screen', u'-ls', name], fail=False, log=log, **kwargs)[u'stdout'], u'utf-8'))


def ssh(host, id=None, remote_cmd=None, fail=True, log=None, **kwargs):
    command = [u'ssh']
    if id is not None:
        command += [u'-i', id]
    command += [host]
    if remote_cmd is not None:
        command += [u'-n', remote_cmd]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)
