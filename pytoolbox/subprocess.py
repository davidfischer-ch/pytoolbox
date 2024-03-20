from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeAlias
import errno
import fcntl
import grp
import logging
import multiprocessing
import os
import pwd
import random
import re
import setuptools.archive_util
import shlex
import shutil
import subprocess
import threading
import time

from . import filesystem, module

_all = module.All(globals())

EMPTY_CMD_RETURN = {'process': None, 'stdout': None, 'stderr': None, 'returncode': None}

# import Popen on steroids if available
try:
    from psutil import NoSuchProcess, Popen
except ImportError:
    from subprocess import Popen
    NoSuchProcess = None

try:
    from shlex import quote
except ImportError:
    from pipes import quote  # pylint: disable=deprecated-module


# Better to warn user than letting converting to string Any!
# None will be stripped automatically
CallArgType: TypeAlias = int | float | str | Path | None
CallArgsType: TypeAlias = str | Iterable[CallArgType]
LoggerType: TypeAlias = Callable | logging.Logger | None


def kill(process):
    try:
        process.kill()
    except OSError as ex:
        if ex.errno != errno.ESRCH:
            raise
    except Exception as ex:  # pylint:disable=broad-except
        if not NoSuchProcess or not isinstance(ex, NoSuchProcess):
            raise


def su(user, group):  # pylint:disable=invalid-name
    """
    Return a function to change current user/group id.

    **Example usage**

    >> import subprocess
    >> subprocess.call(['ls', '/'], preexec_fn=su(1000, 1000))
    >> subprocess.call(['ls', '/'], preexec_fn=su('root', 'root'))
    """
    def set_ids():
        os.setgid(grp.getgrnam(group).gr_gid if isinstance(group, str) else group)
        os.setuid(pwd.getpwnam(user).pw_uid if isinstance(user, str) else user)
    return set_ids


# http://stackoverflow.com/a/7730201/190597
def make_async(fd):  # pylint:disable=invalid-name
    """Add the O_NONBLOCK flag to a file descriptor."""
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# http://stackoverflow.com/a/7730201/190597
def read_async(fd):  # pylint:disable=invalid-name
    """Read some data from a file descriptor, ignoring EAGAIN errors."""
    try:
        return fd.read()
    except IOError as ex:
        if ex.errno == errno.EAGAIN:
            return ''
        raise


def to_args_list(args: CallArgsType | None) -> list[str]:
    if not args:
        return []
    return shlex.split(args) if isinstance(args, str) else [str(a) for a in args if a is not None]


def to_args_string(args: CallArgsType | None) -> str:
    if not args:
        return ''
    return args if isinstance(args, str) else ' '.join(quote(str(a)) for a in args if a is not None)


# --------------------------------------------------------------------------------------------------

def raw_cmd(arguments: CallArgsType, *, shell: bool = False, **kwargs) -> Popen:
    """
    Launch a subprocess.

    This function ensure that:

    * subprocess arguments will be converted to a string if `shell` is True
    * subprocess.args is set to the arguments of the subprocess
    """
    arguments = to_args_list(arguments)
    process = Popen(to_args_string(arguments) if shell else arguments, shell=shell, **kwargs)
    if not hasattr(process, 'args'):
        process.args = arguments
    return process


# thanks http://stackoverflow.com/questions/1191374$
def _communicate_with_timeout(*, data, process, input):  # pylint:disable=redefined-builtin
    data['stdout'], data['stderr'] = process.communicate(input=input)


def cmd(  # pylint:disable=too-many-arguments,too-many-branches,too-many-locals,too-many-statements
    command: CallArgsType,
    *,
    user: str | None = None,
    input: str | None = None,  # pylint:disable=redefined-builtin
    cli_input: str | None = None,
    cli_output: bool = False,
    communicate: bool = True,
    timeout: float | None = None,
    fail: bool = True,
    log: LoggerType = None,
    tries: int = 1,
    delay_min: float = 5,
    delay_max: float = 10,
    **kwargs
) -> dict:
    """
    Calls the `command` and returns a dictionary with process, stdout, stderr, and the returncode.

    Returned returncode, stdout and stderr will be None if `communicate` is set to False.

    :param command: The command to execute.
    :param user: If set, this will use ``sudo -u <user> ...`` to execute `command` as `user`.
    :param input: If set, sended to stdin (if `communicate` is True).
    :param cli_input: If set, sended to stdin (no condition).
    :param cli_output: Set to True to output (in real-time) stdout to stdout and stderr to stderr.
    :param fail: Set to False to avoid the exception `subprocess.CalledProcessError`.
    :param log: A function to log/print details about what is executed/any failure, can be a logger.
    :param communicate: Set to True to communicate with the process, this is a locking call
                        (if timeout is None).
    :param timeout: Time-out for the communication with the process, in seconds.
    :param tries: How many times you want the command to be retried ?
    :param delay_min: Minimum delay to sleep after every attempt communicate must be True.
    :param delay_max: Maximum delay to sleep after every attempt communicate must be True.
    :param kwargs: Any argument of the :mod:`subprocess`.Popen constructor
                   excepting stdin, stdout and stderr

    The delay will be a random number in range (`delay_min`, `delay_max`).

    """

    # Convert log argument to logging functions
    log_debug = log_warning = log_exception = None
    if isinstance(log, logging.Logger):
        log_debug, log_warning, log_exception = log.debug, log.warning, log.exception
    elif hasattr(log, '__call__'):
        log_debug = log_warning = log_exception = log

    # Process arguments
    args_list = to_args_list(command)
    if user is not None:
        args_list = ['sudo', '-u', user, *command]
    args_string = to_args_string(args_list)

    # log the execution
    if log_debug:
        log_debug(''.join([
            'Execute ',
            '' if input is None else f'echo {repr(input)} | ',
            args_string,
            '' if cli_input is None else f' < {repr(cli_input)}'
        ]))

    for trial in range(tries):  # noqa
        # create the sub-process
        try:
            process = Popen(
                args_list,
                stdin=subprocess.PIPE,
                stdout=None if cli_output else subprocess.PIPE,
                stderr=None if cli_output else subprocess.PIPE, **kwargs)
        except OSError as ex:
            # Unable to execute the program (e.g. does not exist)
            if log_exception:
                log_exception(ex)
            if fail:
                raise
            return {'process': None, 'stdout': '', 'stderr': ex, 'returncode': 2}

        # Write to stdin (answer to questions, ...)
        if cli_input is not None:
            process.stdin.write(cli_input)
            process.stdin.flush()

        # Interact with the process and wait for the process to terminate
        if communicate:
            data: dict = {}
            thread = threading.Thread(
                target=_communicate_with_timeout,
                kwargs={'data': data, 'input': input, 'process': process})
            thread.start()
            thread.join(timeout=timeout)
            if thread.is_alive():
                try:
                    process.terminate()
                    thread.join()
                except OSError as ex:
                    # Manage race condition with process that may terminate just after the call to
                    # thread.is_alive() !
                    if ex.errno != errno.ESRCH:
                        raise
            stdout, stderr = data['stdout'], data['stderr']
        else:
            # get a return code that may be None of course ...
            process.poll()
            stdout = stderr = None

        result = {
            'process': process,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': process.returncode
        }

        if process.returncode == 0:
            break

        # failed attempt, may retry
        do_retry = trial < tries - 1
        delay = random.uniform(delay_min, delay_max)
        if log_warning:
            log_warning(' '.join([
                f'Attempt {trial + 1} out of {tries}:',
                f'Will retry in {delay} seconds' if do_retry else 'Failed'
            ]))

        # raise if this is the last try
        if fail and not do_retry:
            raise subprocess.CalledProcessError(process.returncode, args_string, stderr)

        if do_retry:
            time.sleep(delay)

    return result


# --------------------------------------------------------------------------------------------------

def git_add_submodule(
    directory: Path,
    url: str | None = None,
    *,
    remote: str = 'origin',
    fail: bool = True,
    log: LoggerType = None,
    **kwargs
) -> dict:
    if url is not None:
        config = (directory / '.git/config').read_text(encoding='utf-8')
        regex = rf'\[remote "{remote}"\][^\[]+url\s+=\s+(\S+)'
        url = re.search(regex, config, re.MULTILINE).group(1)  # type: ignore[union-attr]
    return cmd(['git', 'submodule', 'add', '-f', url, directory], fail=fail, log=log, **kwargs)


def git_clone_or_pull(
    directory: Path,
    url: str,
    *,
    bare: bool = False,
    clone_depth: int | None = None,
    reset: bool = True,
    fail: bool = True,
    log: LoggerType = None,
    **kwargs
) -> None:
    if directory.exists():
        if reset and not bare:
            cmd(['git', 'reset', '--hard'], cwd=directory, fail=fail, log=log, **kwargs)
        cmd(['git', 'fetch' if bare else 'pull'], cwd=directory, fail=fail, log=log, **kwargs)
    else:
        command: list[CallArgType] = ['git', 'clone']
        if bare:
            command.append('--bare')
        if clone_depth:
            command.extend(['--depth', clone_depth])
        command.extend([url, directory])
        cmd(command, fail=fail, log=log, **kwargs)


# --------------------------------------------------------------------------------------------------

def make(
    archive: Path,
    directory: Path,
    *,
    with_cmake: bool = False,
    configure_options: str = '',
    install: bool = True,
    remove_temporary: bool = True,
    make_options: str = f'-j{multiprocessing.cpu_count()}',
    fail: bool = True,
    log: LoggerType = None,
    **kwargs
) -> dict[str, dict]:
    """Build and optionally install a piece of software from source."""
    results = {}
    setuptools.archive_util.unpack_archive(archive, directory)
    with filesystem.chdir(directory):
        if with_cmake:
            filesystem.makedirs(Path('build'))
            os.chdir('build')
            results['cmake'] = cmd(
                'cmake -DCMAKE_BUILD_TYPE=RELEASE ..',
                fail=fail,
                log=log,
                **kwargs)
        else:
            results['configure'] = cmd(
                f'./configure {configure_options}',
                fail=fail,
                log=log,
                **kwargs)
        results['make'] = cmd(f'make {make_options}', fail=fail, log=log, **kwargs)
        if install:
            results['make install'] = cmd('make install', fail=fail, log=log, **kwargs)
    if remove_temporary:
        shutil.rmtree(directory)

    return results


# --------------------------------------------------------------------------------------------------

def rsync(  # pylint:disable=too-many-arguments,too-many-locals
    source: Path,
    destination: Path,
    *,
    source_is_dir: bool = False,
    destination_is_dir: bool = False,
    archive: bool = True,
    delete: bool = False,
    exclude_vcs: bool = False,
    progress: bool = False,
    recursive: bool = False,
    simulate: bool = False,
    excludes: Iterable[str] | None = None,
    includes: Iterable[str] | None = None,
    rsync_path: Path | None = None,
    size_only: bool = False,
    extra: str | None = None,
    extra_args: list[CallArgType] | None = None,
    fail: bool = True,
    log: LoggerType = None,
    **kwargs
) -> dict:
    """Execute the famous rsync remote (or local) synchronization tool."""
    source_string = str(source)
    if source.is_dir() or source_is_dir:
        source_string += os.sep

    destination_string = str(destination)
    if destination.is_dir() or destination_is_dir:
        destination_string += os.sep

    command: list[CallArgType] = [
        'rsync',
        '-a' if archive else None,
        '--delete' if delete else None,
        '--progress' if progress else None,
        '-r' if recursive else None,
        '--dry-run' if simulate else None,
        '--size-only' if size_only else None
    ]

    if rsync_path is not None:
        command += ['--rsync-path', rsync_path]
    if extra is not None:
        command += ['-e', extra]
    if excludes is not None:
        command += [f'--exclude={e}' for e in excludes]
    if includes is not None:
        command += [f'--include={i}' for i in includes]
    if exclude_vcs:
        command += ['--exclude=.svn', '--exclude=.git']
    if extra_args is not None:
        command += extra_args
    command += [source_string, destination_string]

    return cmd([c for c in command if c], fail=fail, log=log, **kwargs)


def screen_kill(name: str | None = None, *, fail: bool = True, log: LoggerType = None, **kwargs):
    """Kill all screen instances called `name` or all if `name` is None."""
    for instance_name in screen_list(name=name, log=log):
        cmd(['screen', '-S', instance_name, '-X', 'quit'], fail=fail, log=log, **kwargs)


def screen_launch(
    name: str,
    command: CallArgsType,
    *,
    fail: bool = True,
    log: LoggerType = None,
    **kwargs
):
    """Launch a new named screen instance."""
    return cmd(['screen', '-dmS', name, *to_args_list(command)], fail=fail, log=log, **kwargs)


def screen_list(name: str | None = None, *, log: LoggerType = None, **kwargs) -> list[str]:
    """Returns a list containing all instances of screen. Can be filtered by `name`."""
    screens = cmd(['screen', '-ls', name], fail=False, log=log, **kwargs)['stdout']
    return re.findall(r'\s+(\d+.\S+)\s+\(.*\).*', screens.decode('utf-8'))


def ssh(
    host: str,
    identity_file: Path | None = None,
    remote_cmd: str | None = None,
    *,
    fail: bool = True,
    log=None,
    **kwargs
) -> dict:
    command: list[CallArgType] = ['ssh']
    if identity_file is not None:
        command.extend(['-i', identity_file])
    command.append(host)
    if remote_cmd is not None:
        command.extend(['-n', remote_cmd])
    return cmd([c for c in command if c], fail=fail, log=log, **kwargs)


__all__ = _all.diff(globals())
