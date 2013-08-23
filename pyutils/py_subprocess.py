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

import errno, fcntl, os, re, shlex, subprocess
from kitchen.text.converters import to_bytes

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
        return {u'process': process, u'stdout': u'', u'stderr': e, u'returncode': 2}
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

def rsync(source, destination, makedest=False, archive=True, delete=False, exclude_vcs=False,
          progress=False, recursive=False, simulate=False, excludes=None, includes=None, fail=True,
          log=None, **kwargs):
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
    if excludes is not None:
        command.extend([u'--exclude={0}'.format(e) for e in excludes])
    if includes is not None:
        command.extend([u'--include={0}'.format(i) for i in includes])
    if exclude_vcs:
        command.extend([u'--exclude=.svn', u'--exclude=.git'])
    command.extend([source, destination])
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
    return re.findall(ur'\s+(\d+.\S+)\s+\(.*\).*',
                      cmd([u'screen', u'-ls', name], fail=False, log=log, **kwargs)[u'stdout'])
