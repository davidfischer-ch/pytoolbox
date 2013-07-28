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

import errno, fcntl, os, re, shlex, subprocess


def cmd(command, input=None, cli_input=None, shell=False, fail=True, log=None):
    u"""
    Calls the ``command`` and returns a dictionary with stdout, stderr, and the returncode.

    * Pipe some content to the command with ``input``.
    * Answer to interactive CLI questions with ``cli_input``.
    * Set ``fail`` to False to avoid the exception ``subprocess.CalledProcessError``.
    * Set ``shell`` to True to enable shell expansion (dangerous ! See :mod:`subprocess`).
    * Set ``log`` to a method to log / print details about what is executed / any failure.
    """
    if log is not None:
        log(u'Execute {}{}{}'.format(u'' if input is None else u'echo {} | '.format(repr(input)),
            command, u'' if cli_input is None else u' < {}'.format(repr(cli_input))))
    args = filter(None, command if isinstance(command, list) else shlex.split(command))
    try:
        process = subprocess.Popen(args, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError as e:
        if fail:
            raise
        return {u'stdout': u'', u'stderr': e, u'returncode': 2}
    if cli_input is not None:
        process.stdin.write(cli_input)
    stdout, stderr = process.communicate(input=input)
    result = {u'stdout': stdout, u'stderr': stderr, u'returncode': process.returncode}
    if fail and process.returncode != 0:
        if log is not None:
            log(result)
        raise subprocess.CalledProcessError(process.returncode, command, stderr)
    return result


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
          log=None):
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
        command.extend([u'--exclude={}'.format(e) for e in excludes])
    if includes is not None:
        command.extend([u'--include={}'.format(i) for i in includes])
    if exclude_vcs:
        command.extend([u'--exclude=.svn', u'--exclude=.git'])
    command.extend([source, destination])
    return cmd(filter(None, command), fail=fail, log=log)


def screen_kill(name=None, fail=True, log=None):
    u"""
    Kill all screen instances called ``name`` or all if ``name`` is None.
    """
    for name in screen_list(name=name, log=log):
        cmd([u'screen', u'-S', name, u'-X', u'quit'], fail=fail, log=log)


def screen_launch(name, command, fail=True, log=None):
    u"""
    Launch a new named screen instance.
    """
    return cmd([u'screen', u'-dmS', name] + (command if isinstance(command, list) else [command]),
               fail=fail, log=log)


def screen_list(name=None, log=None):
    u"""
    Returns a list containing all instances of screen. Can be filtered by ``name``.
    """
    return re.findall(r'\s+(\d+.\S+)\s+\(.*\).*',
                      cmd([u'screen', u'-ls', name], fail=False, log=log)[u'stdout'])
