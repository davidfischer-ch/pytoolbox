# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
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
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, fcntl, logging, multiprocessing, os, random, re
from os.path import exists, isdir, normpath
import setuptools.archive_util, shlex, shutil, subprocess, threading, time
from .encoding import to_bytes, string_types
from .filesystem import try_makedirs

EMPTY_CMD_RETURN = {u'process': None, u'stdout': None, u'stderr': None, u'returncode': None}


def cmd(command, user=None, input=None, cli_input=None, cli_output=False, communicate=True, timeout=None, fail=True,
        log=None, tries=1, delay_min=5, delay_max=10, **kwargs):
    u"""
    Calls the ``command`` and returns a dictionary with process, stdout, stderr, and the returncode.

    Returned returncode, stdout and stderr will be None if ``communicate`` is set to False.

    :param user: If set, this will use ``sudo -u <user> ...`` to execute ``command`` as ``user``.
    :type user: unicode
    :param input: If set, sended to stdin (if ``communicate`` is True).
    :type input: unicode
    :param cli_input: If set, sended to stdin (no condition).
    :type cli_input: unicode
    :param cli_output: Set to True to output (in real-time) stdout to stdout and stderr to stderr.
    :type cli_output: bool
    :param fail: Set to False to avoid the exception ``subprocess.CalledProcessError``.
    :type fail: bool
    :param log: A method to log/print details about what is executed/any failure, can be a standard logger.
    :type log: callable, logging.Logger
    :param communicate: Set to True to communicate with the process, this is a locking call (if timeout is None).
    :type communicate: bool
    :param timeout: Time-out for the communication with the process, in seconds.
    :type timeout: float
    :param tries: How many times you want the command to be retried ?
    :type tries: int
    :param delay_min: Minimum delay to sleep after every attempt communicate must be True.
    :type delay: float, int
    :param delay_max: Maximum delay to sleep after every attempt communicate must be True.
    :type delay: float, int

    * Delay will be a random number in range (``delay_min``, ``delay_max``)
    * Set kwargs with any argument of the :mod:`subprocess`.Popen constructor excepting stdin, stdout and stderr.

    """
    # convert log argument to logging methods
    log_debug = log_warning = log_exception = None
    if isinstance(log, logging.Logger):
        log_debug, log_warning, log_exception = log.debug, log.warning, log.exception
    elif hasattr(log, u'__call__'):
        log_debug = log_warning = log_exception = log
    # create a list and a string of the arguments
    if isinstance(command, string_types):
        if user:
            command = u'sudo -u {0} {1}'.format(user, command)
        args_list, args_string = shlex.split(to_bytes(command)), command
    else:
        if user:
            command = [u'sudo', u'-u', user] + command
        args_list = [to_bytes(a) for a in command if a is not None]
        args_string = u' '.join([unicode(a) for a in command if a is not None])
    # log the execution
    if log_debug:
        log_debug(u'Execute {0}{1}{2}'.format(u'' if input is None else u'echo {0}|'.format(repr(input)),
                  args_string, u'' if cli_input is None else u' < {0}'.format(repr(cli_input))))

    for trial in range(tries):
        # create the sub-process
        try:
            process = subprocess.Popen(args_list, stdin=subprocess.PIPE, stdout=None if cli_output else subprocess.PIPE,
                                       stderr=None if cli_output else subprocess.PIPE, **kwargs)
        except OSError as e:
            # unable to execute the program (e.g. does not exist)
            if log_exception:
                log_exception(e)
            if fail:
                raise
            return {u'process': None, u'stdout': u'', u'stderr': e, u'returncode': 2}
        # write to stdin (answer to questions, ...)
        if cli_input is not None:
            process.stdin.write(to_bytes(cli_input))
            process.stdin.flush()
        # interact with the process and wait for the process to terminate
        if communicate:
            data = {}
            # thanks http://stackoverflow.com/questions/1191374/subprocess-with-timeout
            def communicate_with_timeout(data=None):
                data[u'stdout'], data[u'stderr'] = process.communicate(input=input)
            thread = threading.Thread(target=communicate_with_timeout, kwargs={u'data': data})
            thread.start()
            thread.join(timeout=timeout)
            if thread.is_alive():
                try:
                    process.terminate()
                    thread.join()
                except OSError as e:
                    # Manage race condition with process that may terminate just after the call to thread.is_alive() !
                    if e.errno != errno.ESRCH:
                        raise
            stdout, stderr = data[u'stdout'], data[u'stderr']
        else:
            # get a return code that may be None of course ...
            process.poll()
            stdout = stderr = None
        result = {u'process': process, u'stdout': stdout, u'stderr': stderr, u'returncode': process.returncode}
        if process.returncode == 0:
            break
        # failed attempt, may retry
        do_retry = trial < tries - 1
        delay = random.uniform(delay_min, delay_max)
        if log_warning:
            log_warning(u'Attempt {0} out of {1}: {2}'.format(trial+1, tries,
                        u'Will retry in {0} seconds'.format(delay) if do_retry else u'Failed'))
        # raise if this is the last try
        if fail and not do_retry:
            raise subprocess.CalledProcessError(process.returncode, args_string, stderr)
        if do_retry:
            time.sleep(delay)

    return result


# http://stackoverflow.com/a/7730201/190597
def make_async(fd):
    u"""Add the O_NONBLOCK flag to a file descriptor."""
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# http://stackoverflow.com/a/7730201/190597
def read_async(fd):
    u"""Read some data from a file descriptor, ignoring EAGAIN errors."""
    try:
        return fd.read()
    except IOError as e:
        if e.errno == errno.EAGAIN:
            return u''
        raise

# ----------------------------------------------------------------------------------------------------------------------

def make(archive, path=None, with_cmake=False, configure_options=u'', install=True, remove_temporary=True,
         make_options=u'-j{0}'.format(multiprocessing.cpu_count()), fail=True, log=None, **kwargs):
    results = {}
    here = os.getcwd()
    path = path or archive.split(u'.')[0]
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

# ----------------------------------------------------------------------------------------------------------------------

def rsync(source, destination, source_is_dir=False, destination_is_dir=False, makedest=False, archive=True,
          delete=False, exclude_vcs=False, progress=False, recursive=False, simulate=False, excludes=None,
          includes=None, rsync_path=None, size_only=False, extra=None, extra_args=None, fail=True, log=None, **kwargs):
    if makedest and not exists(destination):
        # FIXME if dest = remote -> ssh to make dest else make dest
        if u'ssh' not in extra:
            os.makedirs(destination)
    source = normpath(source) + (os.sep if isdir(source) or source_is_dir else u'')
    destination = normpath(destination) + (os.sep if isdir(destination) or destination_is_dir else u'')
    command = [u'rsync',
               u'-a' if archive else None,
               u'--delete' if delete else None,
               u'--progress' if progress else None,
               u'-r' if recursive else None,
               u'--dry-run' if simulate else None,
               u'--size-only' if size_only else None]
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
    if extra_args:
        command += extra_args
    command += [source, destination]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)


def screen_kill(name=None, fail=True, log=None, **kwargs):
    u"""Kill all screen instances called ``name`` or all if ``name`` is None."""
    for name in screen_list(name=name, log=log):
        cmd([u'screen', u'-S', name, u'-X', u'quit'], fail=fail, log=log, **kwargs)


def screen_launch(name, command, fail=True, log=None, **kwargs):
    u"""Launch a new named screen instance."""
    return cmd([u'screen', u'-dmS', name] + (command if isinstance(command, list) else [command]),
               fail=fail, log=log, **kwargs)


def screen_list(name=None, log=None, **kwargs):
    u"""Returns a list containing all instances of screen. Can be filtered by ``name``."""
    screens = cmd([u'screen', u'-ls', name], fail=False, log=log, **kwargs)[u'stdout']
    return re.findall(ur'\s+(\d+.\S+)\s+\(.*\).*', unicode(screens))


def ssh(host, id=None, remote_cmd=None, fail=True, log=None, **kwargs):
    command = [u'ssh']
    if id is not None:
        command += [u'-i', id]
    command += [host]
    if remote_cmd is not None:
        command += [u'-n', remote_cmd]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)
