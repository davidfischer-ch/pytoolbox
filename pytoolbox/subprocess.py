# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import errno, fcntl, grp, logging, multiprocessing, os, pwd, random, re
import setuptools.archive_util, shlex, shutil, subprocess, threading, time

from . import module
from .encoding import string_types, to_bytes, to_unicode
from .filesystem import makedirs

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
    from pipes import quote


def kill(process):
    try:
        process.kill()
    except OSError as e:
        if e.errno != errno.ESRCH:
            raise
    except Exception as e:
        if not NoSuchProcess or not isinstance(e, NoSuchProcess):
            raise


def su(user, group):
    """
    Return a function to change current user/group id.

    **Example usage**

    >> import subprocess
    >> subprocess.call(['ls', '/'], preexec_fn=su(1000, 1000))
    >> subprocess.call(['ls', '/'], preexec_fn=su('root', 'root'))
    """
    def set_ids():
        os.setgid(grp.getgrnam(group).gr_gid if isinstance(group, string_types) else group)
        os.setuid(pwd.getpwnam(user).pw_uid if isinstance(user, string_types) else user)
    return set_ids


# http://stackoverflow.com/a/7730201/190597
def make_async(fd):
    """Add the O_NONBLOCK flag to a file descriptor."""
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# http://stackoverflow.com/a/7730201/190597
def read_async(fd):
    """Read some data from a file descriptor, ignoring EAGAIN errors."""
    try:
        return fd.read()
    except IOError as e:
        if e.errno == errno.EAGAIN:
            return ''
        raise


def to_args_list(args):
    if not args:
        return []
    return shlex.split(args) if isinstance(args, string_types) else ['%s' % a for a in args]


def to_args_string(args):
    if not args:
        return ''
    return args if isinstance(args, string_types) else ' '.join(quote('%s' % a) for a in args)


# --------------------------------------------------------------------------------------------------

def raw_cmd(arguments, shell=False, **kwargs):
    """
    Launch a subprocess.

    This function ensure that:

    * subprocess arguments will be converted to a string if `shell` is True
    * subprocess.args is set to the arguments of the subprocess
    """
    arguments_list = to_args_list(arguments)
    process = Popen(
        to_args_string(arguments_list) if shell else arguments_list, shell=shell, **kwargs)
    if not hasattr(process, 'args'):
        process.args = arguments_list
    return process


def cmd(command, user=None, input=None, cli_input=None, cli_output=False, communicate=True,
        timeout=None, fail=True, log=None, tries=1, delay_min=5, delay_max=10, **kwargs):
    """
    Calls the `command` and returns a dictionary with process, stdout, stderr, and the returncode.

    Returned returncode, stdout and stderr will be None if `communicate` is set to False.

    :param user: If set, this will use ``sudo -u <user> ...`` to execute `command` as `user`.
    :type user: unicode
    :param input: If set, sended to stdin (if `communicate` is True).
    :type input: unicode
    :param cli_input: If set, sended to stdin (no condition).
    :type cli_input: unicode
    :param cli_output: Set to True to output (in real-time) stdout to stdout and stderr to stderr.
    :type cli_output: bool
    :param fail: Set to False to avoid the exception `subprocess.CalledProcessError`.
    :type fail: bool
    :param log: A function to log/print details about what is executed/any failure, can be a logger.
    :type log: callable, logging.Logger
    :param communicate: Set to True to communicate with the process, this is a locking call
                        (if timeout is None).
    :type communicate: bool
    :param timeout: Time-out for the communication with the process, in seconds.
    :type timeout: float
    :param tries: How many times you want the command to be retried ?
    :type tries: int
    :param delay_min: Minimum delay to sleep after every attempt communicate must be True.
    :type delay: float, int
    :param delay_max: Maximum delay to sleep after every attempt communicate must be True.
    :type delay: float, int

    * Delay will be a random number in range (`delay_min`, `delay_max`)
    * Set kwargs with any argument of the :mod:`subprocess`.Popen constructor excepting
      stdin, stdout and stderr.

    """
    # convert log argument to logging functions
    log_debug = log_warning = log_exception = None
    if isinstance(log, logging.Logger):
        log_debug, log_warning, log_exception = log.debug, log.warning, log.exception
    elif hasattr(log, '__call__'):
        log_debug = log_warning = log_exception = log
    # create a list and a string of the arguments
    if isinstance(command, string_types):
        if user is not None:
            command = 'sudo -u {0} {1}'.format(user, command)
        args_list, args_string = shlex.split(to_bytes(command)), command
    else:
        if user is not None:
            command = ['sudo', '-u', user] + command
        args_list = [to_bytes(a) for a in command if a is not None]
        args_string = ' '.join([to_unicode(a) for a in command if a is not None])
    # log the execution
    if log_debug:
        log_debug('Execute {0}{1}{2}'.format(
            '' if input is None else 'echo {0}|'.format(repr(input)),
            args_string,
            '' if cli_input is None else ' < {0}'.format(repr(cli_input))))

    for trial in xrange(tries):  # noqa
        # create the sub-process
        try:
            process = Popen(
                args_list,
                stdin=subprocess.PIPE,
                stdout=None if cli_output else subprocess.PIPE,
                stderr=None if cli_output else subprocess.PIPE, **kwargs)
        except OSError as e:
            # unable to execute the program (e.g. does not exist)
            if log_exception:
                log_exception(e)
            if fail:
                raise
            return {'process': None, 'stdout': '', 'stderr': e, 'returncode': 2}
        # write to stdin (answer to questions, ...)
        if cli_input is not None:
            process.stdin.write(to_bytes(cli_input))
            process.stdin.flush()
        # interact with the process and wait for the process to terminate
        if communicate:
            data = {}

            # thanks http://stackoverflow.com/questions/1191374/subprocess-with-timeout
            def communicate_with_timeout(data=None):
                data['stdout'], data['stderr'] = process.communicate(input=input)
            thread = threading.Thread(target=communicate_with_timeout, kwargs={'data': data})
            thread.start()
            thread.join(timeout=timeout)
            if thread.is_alive():
                try:
                    process.terminate()
                    thread.join()
                except OSError as e:
                    # Manage race condition with process that may terminate just after the call to
                    # thread.is_alive() !
                    if e.errno != errno.ESRCH:
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
            log_warning('Attempt {0} out of {1}: {2}'.format(trial+1, tries,
                        'Will retry in {0} seconds'.format(delay) if do_retry else 'Failed'))
        # raise if this is the last try
        if fail and not do_retry:
            raise subprocess.CalledProcessError(process.returncode, args_string, stderr)
        if do_retry:
            time.sleep(delay)

    return result


# --------------------------------------------------------------------------------------------------

def git_add_submodule(directory, url=None, remote='origin', fail=True, log=None, **kwargs):
    if url is not None:
        config = open(os.path.join(directory, '.git', 'config')).read()
        url = re.search(
            r'\[remote "{0}"\][^\[]+url\s+=\s+(\S+)'.format(remote), config, re.MULTILINE).group(1)
    return cmd(['git', 'submodule', 'add', '-f', url, directory], fail=fail, log=log, **kwargs)


def git_clone_or_pull(directory, url, bare=False, clone_depth=None, reset=True, fail=True, log=None,
                      **kwargs):
    if os.path.exists(directory):
        if reset and not bare:
            cmd(['git', 'reset', '--hard'], cwd=directory, fail=fail, log=log, **kwargs)
        cmd(['git', 'fetch' if bare else 'pull'], cwd=directory, fail=fail, log=log, **kwargs)
    else:
        command = ['git', 'clone']
        if bare:
            command.append('--bare')
        if clone_depth:
            command.extend(['--depth', clone_depth])
        command.extend([url, directory])
        cmd(command, fail=fail, log=log, **kwargs)


# --------------------------------------------------------------------------------------------------

def make(archive, path=None, with_cmake=False, configure_options='', install=True,
         remove_temporary=True, make_options='-j{0}'.format(multiprocessing.cpu_count()), fail=True,
         log=None, **kwargs):
    results = {}
    here = os.getcwd()
    path = path or archive.split('.')[0]
    shutil.rmtree(path, ignore_errors=True)
    setuptools.archive_util.unpack_archive(archive, path)
    os.chdir(path)
    if with_cmake:
        makedirs('build')
        os.chdir('build')
        results['cmake'] = cmd('cmake -DCMAKE_BUILD_TYPE=RELEASE ..', fail=fail, log=log, **kwargs)
    else:
        results['configure'] = cmd(
            './configure {0}'.format(configure_options), fail=fail, log=log, **kwargs)
    results['make'] = cmd('make {0}'.format(make_options), fail=fail, log=log, **kwargs)
    if install:
        results['make install'] = cmd('make install', fail=fail, log=log, **kwargs)
    os.chdir(here)
    if remove_temporary:
        shutil.rmtree(path)
    return results


# --------------------------------------------------------------------------------------------------

def rsync(source, destination, source_is_dir=False, destination_is_dir=False, makedest=False,
          archive=True, delete=False, exclude_vcs=False, progress=False, recursive=False,
          simulate=False, excludes=None, includes=None, rsync_path=None, size_only=False,
          extra=None, extra_args=None, fail=True, log=None, **kwargs):
    if makedest and not os.path.exists(destination):
        # FIXME if dest = remote -> ssh to make dest else make dest
        if extra is None or 'ssh' not in extra:
            os.makedirs(destination)
    source = os.path.normpath(source) + (os.sep if os.path.isdir(source) or source_is_dir else '')
    destination = os.path.normpath(destination) + \
        (os.sep if os.path.isdir(destination) or destination_is_dir else '')
    command = ['rsync',
               '-a' if archive else None,
               '--delete' if delete else None,
               '--progress' if progress else None,
               '-r' if recursive else None,
               '--dry-run' if simulate else None,
               '--size-only' if size_only else None]
    if rsync_path is not None:
        command += ['--rsync-path', rsync_path]
    if extra is not None:
        command += ['-e', extra]
    if excludes is not None:
        command += ['--exclude={0}'.format(e) for e in excludes]
    if includes is not None:
        command += ['--include={0}'.format(i) for i in includes]
    if exclude_vcs:
        command += ['--exclude=.svn', '--exclude=.git']
    if extra_args is not None:
        command += extra_args
    command += [source, destination]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)


def screen_kill(name=None, fail=True, log=None, **kwargs):
    """Kill all screen instances called `name` or all if `name` is None."""
    for name in screen_list(name=name, log=log):
        cmd(['screen', '-S', name, '-X', 'quit'], fail=fail, log=log, **kwargs)


def screen_launch(name, command, fail=True, log=None, **kwargs):
    """Launch a new named screen instance."""
    return cmd(
        ['screen', '-dmS', name] + (command if isinstance(command, list) else [command]),
        fail=fail, log=log, **kwargs)


def screen_list(name=None, log=None, **kwargs):
    """Returns a list containing all instances of screen. Can be filtered by `name`."""
    screens = cmd(['screen', '-ls', name], fail=False, log=log, **kwargs)['stdout']
    return re.findall(r'\s+(\d+.\S+)\s+\(.*\).*', to_unicode(screens))


def ssh(host, id=None, remote_cmd=None, fail=True, log=None, **kwargs):
    command = ['ssh']
    if id is not None:
        command += ['-i', id]
    command += [host]
    if remote_cmd is not None:
        command += ['-n', remote_cmd]
    return cmd(filter(None, command), fail=fail, log=log, **kwargs)


__all__ = _all.diff(globals())
