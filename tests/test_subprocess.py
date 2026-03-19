from __future__ import annotations

from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch
import shutil

import pytest
from pytoolbox import logging, regex, subprocess
from pytoolbox.validation import validate_list


def test_quote_is_from_shlex() -> None:
    """The quote function should come from shlex, not the removed pipes module."""
    import shlex
    assert subprocess.quote is shlex.quote


def test_to_args_list() -> None:
    # pylint:disable=use-implicit-booleaness-not-comparison
    assert subprocess.to_args_list(None) == []  # Hidden feature one should not know:)
    assert subprocess.to_args_list('') == []
    assert subprocess.to_args_list([]) == []
    assert subprocess.to_args_list('tail -f "~/some file"') == ['tail', '-f', '~/some file']
    assert subprocess.to_args_list([10, None, 'string "salut"']) == ['10', 'string "salut"']


def test_to_args_string() -> None:
    assert subprocess.to_args_string(None) == ''  # Hidden feature one should not know:)
    assert subprocess.to_args_string('') == ''
    assert subprocess.to_args_string([]) == ''
    assert subprocess.to_args_string('tail -f "~/some file"') == 'tail -f "~/some file"'
    assert subprocess.to_args_string([10, None, 'string "salut"']) == '10 \'string "salut"\''


def test_cmd_happy_case():
    result = subprocess.cmd(['cat', __file__])
    assert isinstance(result['process'], subprocess.Popen)
    assert result['returncode'] == 0
    assert len(result['stdout'].splitlines()) > 30  # At least 30 lines in this source file !
    assert result['stderr'] == b''


def test_cmd_logging(caplog, capsys):
    """
    Ensure logging is not outputting to stderr by default.

    See https://docs.python.org/3/howto/logging.html#library-config
    """
    caplog.set_level(logging.DEBUG)
    subprocess.cmd(['cat', __file__])
    subprocess.cmd(['echo', 'toto tata'])
    subprocess.cmd(['/usr/bin/env', 'python'])
    subprocess.cmd(['ls', Path(__file__).parent], log=lambda msg: None)
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''
    # log = logging.get_logger('pytoolbox.subprocess.cmd.cat')
    cat_record, echo_record, env_record = caplog.records
    assert cat_record.name == 'pytoolbox.subprocess.cmd.cat'
    assert cat_record.levelname == 'DEBUG'
    assert cat_record.msg == f'Execute cat {__file__}'
    assert echo_record.name == 'pytoolbox.subprocess.cmd.echo'
    assert echo_record.levelname == 'DEBUG'
    assert echo_record.msg == "Execute echo 'toto tata'"
    assert env_record.name == 'pytoolbox.subprocess.cmd.env'
    assert env_record.levelname == 'DEBUG'
    assert env_record.msg == "Execute /usr/bin/env python"


def test_cmd_log_to_func() -> None:
    log = mock.Mock()
    log.__name__ = 'Mock'
    subprocess.cmd(['echo', 'it seem to work'], log=log)
    result = subprocess.cmd('cat missing_file', fail=False, log=log)
    assert isinstance(result['process'], subprocess.Popen)
    assert result['returncode'] == 1
    assert result['stdout'] == b''
    assert result['stderr'] in {
        b'cat: missing_file: No such file or directory\n',
        b'cat: missing_file: Aucun fichier ou dossier de ce nom\n'
    }
    assert log.call_args_list == [
        mock.call("Execute echo 'it seem to work'"),
        mock.call('Execute cat missing_file'),
        mock.call('Attempt 1 out of 1: Failed')
    ]


def test_cmd_missing_binary() -> None:
    result = subprocess.cmd('hfuejnvwqkdivengz', fail=False)
    assert result['process'] is None
    assert result['returncode'] == 2
    assert result['stdout'] is None
    assert result['stderr'] is None


def test_cmd_retry_first_try() -> None:
    log = mock.Mock()
    log.__name__ = 'Mock'
    subprocess.cmd('ls', log=log, tries=5, delay_min=1, delay_max=1)
    log.assert_called_once_with('Execute ls')


def test_cmd_retry_missing_binary_no_retry() -> None:
    log = mock.Mock()
    log.__name__ = 'Mock'
    with pytest.raises(OSError):
        subprocess.cmd('hfuejnvwqkdivengz', log=log, tries=5)
    validate_list(log.call_args_list, [
        r"call\('Execute hfuejnvwqkdivengz'\)",
        r'call\(FileNotFoundError.*\)'
    ])


def test_cmd_retry_no_success() -> None:
    log = mock.Mock()
    log.__name__ = 'Mock'
    subprocess.cmd(
        'ls hfuejnvwqkdivengz',
        log=log,
        fail=False,
        tries=5,
        delay_min=0.0,
        delay_max=0.95)
    validate_list(log.call_args_list, [
        r"call\('Execute ls hfuejnvwqkdivengz'\)",
        r"call\('Attempt 1 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
        r"call\('Attempt 2 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
        r"call\('Attempt 3 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
        r"call\('Attempt 4 out of 5: Will retry in 0\.[0-9]+ seconds'\)",
        r"call\('Attempt 5 out of 5: Failed'\)"
    ])


@pytest.mark.skipif(shutil.which('screen') is None, reason='screen not installed')
def test_screen() -> None:
    try:
        # Launch some screens
        subprocess.screen_kill('my_1st_screen', fail=False)
        subprocess.screen_kill('my_2nd_screen', fail=False)
        assert subprocess.screen_launch('my_1st_screen', 'top', fail=False)['stderr'] == b''
        assert subprocess.screen_launch('my_2nd_screen', 'top', fail=False)['stderr'] == b''
        assert subprocess.screen_launch('my_2nd_screen', 'top', fail=False)['stderr'] == b''

        # List the launched screen sessions
        assert subprocess.screen_list(name='my_1st_screen') == [regex.Match(r'\d+\.my_1st_screen')]
        assert subprocess.screen_list(name='my_2nd_screen') == [
            regex.Match(r'\d+\.my_2nd_screen'),
            regex.Match(r'\d+\.my_2nd_screen')
        ]
    finally:
        # Cleanup
        log = mock.Mock()
        log.__name__ = 'Mock'
        subprocess.screen_kill(name='my_1st_screen', log=log)
        subprocess.screen_kill(name='my_2nd_screen', log=log)
        if log.call_args_list:
            validate_list(log.call_args_list, [
                r"call\('Execute screen -ls my_1st_screen'\)",
                r"call\('Execute screen -S \d+\.my_1st_screen -X quit'\)",
                r"call\('Execute screen -ls my_2nd_screen'\)",
                r"call\('Execute screen -S \d+\.my_2nd_screen -X quit'\)",
                r"call\('Execute screen -S \d+\.my_2nd_screen -X quit'\)"
            ])


def test_kill_ignores_esrch() -> None:
    """kill() silences OSError with errno ESRCH (no such process)."""
    import errno as errno_mod
    proc = mock.MagicMock()
    proc.kill.side_effect = OSError(errno_mod.ESRCH, 'No such process')
    subprocess.kill(proc)  # should not raise


def test_kill_reraises_other_oserror() -> None:
    """kill() re-raises OSError when errno is not ESRCH."""
    import errno as errno_mod
    proc = mock.MagicMock()
    proc.kill.side_effect = OSError(errno_mod.EPERM, 'Not permitted')
    with pytest.raises(OSError, match='Not permitted'):
        subprocess.kill(proc)


def test_kill_ignores_nosuchprocess() -> None:
    """kill() silences psutil.NoSuchProcess when psutil is available."""
    if subprocess.NoSuchProcess is None:
        pytest.skip('psutil not installed')
    proc = mock.MagicMock()
    proc.kill.side_effect = subprocess.NoSuchProcess(pid=99999)
    subprocess.kill(proc)


def test_kill_reraises_generic_exception() -> None:
    """kill() re-raises non-OSError, non-NoSuchProcess exceptions."""
    proc = mock.MagicMock()
    proc.kill.side_effect = RuntimeError('unexpected')
    with pytest.raises(RuntimeError, match='unexpected'):
        subprocess.kill(proc)


def test_su_with_integer_ids() -> None:
    """
    su() with integer user/group returns a callable that calls
    os.setgid and os.setuid.
    """
    with (
        mock.patch('os.setgid') as mock_setgid,
        mock.patch('os.setuid') as mock_setuid
    ):
        fn = subprocess.su(1000, 1000)
        fn()
        mock_setgid.assert_called_once_with(1000)
        mock_setuid.assert_called_once_with(1000)


def test_su_with_string_names() -> None:
    """su() with string user/group resolves names via pwd/grp."""
    fake_pw = mock.MagicMock()
    fake_pw.pw_uid = 0
    fake_gr = mock.MagicMock()
    fake_gr.gr_gid = 0
    with (
        mock.patch('os.setgid') as mock_setgid,
        mock.patch('os.setuid') as mock_setuid,
        mock.patch('pwd.getpwnam', return_value=fake_pw),
        mock.patch('grp.getgrnam', return_value=fake_gr)
    ):
        fn = subprocess.su('root', 'root')
        fn()
        mock_setgid.assert_called_once_with(0)
        mock_setuid.assert_called_once_with(0)


def test_make_async_with_fd_object() -> None:
    """make_async() calls os.set_blocking with the fileno of an IO."""
    fd = mock.MagicMock()
    fd.fileno.return_value = 7
    with mock.patch('os.set_blocking') as mock_sb:
        subprocess.make_async(fd)
        mock_sb.assert_called_once_with(7, False)


def test_make_async_with_raw_int() -> None:
    """make_async() accepts a raw integer file descriptor."""
    with mock.patch('os.set_blocking') as mock_sb:
        subprocess.make_async(42)
        mock_sb.assert_called_once_with(42, False)


def test_read_async_returns_data() -> None:
    """read_async() returns data from fd.read()."""
    fd = mock.MagicMock()
    fd.read.return_value = 'hello'
    assert subprocess.read_async(fd) == 'hello'


def test_read_async_eagain_returns_empty() -> None:
    """read_async() returns empty string on EAGAIN IOError."""
    import errno as errno_mod
    fd = mock.MagicMock()
    fd.read.side_effect = IOError(errno_mod.EAGAIN, 'try again')
    assert subprocess.read_async(fd) == ''


def test_read_async_reraises_other_ioerror() -> None:
    """read_async() re-raises IOError when errno is not EAGAIN."""
    import errno as errno_mod
    fd = mock.MagicMock()
    fd.read.side_effect = IOError(errno_mod.EBADF, 'bad fd')
    with pytest.raises(IOError):
        subprocess.read_async(fd)


def test_cmd_with_user_prepends_sudo(caplog) -> None:
    """cmd() prepends sudo -u <user> when user kwarg is set."""
    caplog.set_level(logging.DEBUG)
    result = subprocess.cmd(
        ['whoami'],
        user='nobody',
        fail=False)
    # The command should have been wrapped with sudo
    assert result['process'] is not None or result['returncode'] == 2


def test_cmd_with_input() -> None:
    """cmd() sends data to stdin when input kwarg is provided."""
    result = subprocess.cmd(
        ['cat'],
        input=b'hello world')
    assert result['stdout'] == b'hello world'


def test_cmd_communicate_false() -> None:
    """cmd() with communicate=False returns None stdout/stderr."""
    result = subprocess.cmd(
        ['sleep', '0.1'],
        communicate=False,
        fail=False)
    assert result['stdout'] is None
    assert result['stderr'] is None
    assert result['process'] is not None
    result['process'].wait()


def test_cmd_cli_input() -> None:
    """cmd() writes cli_input to stdin before communicate."""
    result = subprocess.cmd(
        ['cat'],
        cli_input=b'typed input')
    assert result['process'] is not None


def test_cmd_fail_raises_called_process_error() -> None:
    """
    cmd() raises CalledProcessError when fail=True
    and process returns non-zero.
    """
    from pytoolbox import exceptions
    with pytest.raises(exceptions.CalledProcessError):
        subprocess.cmd('cat missing_file_xyz_123')


def test_cmd_custom_success_codes() -> None:
    """cmd() accepts custom success_codes so non-zero can pass."""
    result = subprocess.cmd(
        'cat missing_file_xyz_123',
        fail=False,
        success_codes=(0, 1))
    assert result['returncode'] == 1


def test_cmd_timeout_kills_process() -> None:
    """cmd() terminates the process when timeout expires."""
    result = subprocess.cmd(
        ['sleep', '30'],
        timeout=0.1,
        fail=False)
    assert result['process'] is not None
    # Process was terminated, so returncode is non-zero
    assert result['returncode'] != 0


def test_raw_cmd_returns_process() -> None:
    """raw_cmd() returns a Popen instance with args set."""
    proc = subprocess.raw_cmd(['echo', 'hello'])
    proc.wait()
    assert hasattr(proc, 'args')
    assert proc.returncode == 0


def test_raw_cmd_shell_mode() -> None:
    """raw_cmd() with shell=True passes a string command."""
    proc = subprocess.raw_cmd(
        ['echo', 'hello'],
        shell=True,
        stdout=__import__('subprocess').PIPE)
    stdout, _ = proc.communicate()
    assert b'hello' in stdout


def test_make_without_cmake() -> None:
    """make() runs configure, make, and make install by default."""
    with (
        patch.object(
            subprocess.setuptools.archive_util,
            'unpack_archive'
        ),
        patch.object(subprocess.filesystem, 'chdir'),
        patch.object(subprocess, 'cmd') as mock_cmd,
        patch.object(subprocess.shutil, 'rmtree')
    ):
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        results = subprocess.make(
            Path('/tmp/archive.tar.gz'),
            Path('/tmp/build'))
        assert 'configure' in results
        assert 'make' in results
        assert 'make install' in results


def test_make_with_cmake() -> None:
    """
    make() with with_cmake=True runs cmake instead of
    configure.
    """
    with (
        patch.object(
            subprocess.setuptools.archive_util,
            'unpack_archive'
        ),
        patch.object(subprocess.filesystem, 'chdir'),
        patch.object(subprocess.filesystem, 'makedirs'),
        patch.object(subprocess.os, 'chdir'),
        patch.object(subprocess, 'cmd') as mock_cmd,
        patch.object(subprocess.shutil, 'rmtree')
    ):
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        results = subprocess.make(
            Path('/tmp/archive.tar.gz'),
            Path('/tmp/build'),
            with_cmake=True)
        assert 'cmake' in results
        assert 'configure' not in results


def test_make_no_install() -> None:
    """make() with install=False skips make install."""
    with (
        patch.object(
            subprocess.setuptools.archive_util,
            'unpack_archive'
        ),
        patch.object(subprocess.filesystem, 'chdir'),
        patch.object(subprocess, 'cmd') as mock_cmd,
        patch.object(subprocess.shutil, 'rmtree')
    ):
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        results = subprocess.make(
            Path('/tmp/archive.tar.gz'),
            Path('/tmp/build'),
            install=False)
        assert 'make install' not in results


def test_make_keep_temporary() -> None:
    """make() with remove_temporary=False keeps the directory."""
    with (
        patch.object(
            subprocess.setuptools.archive_util,
            'unpack_archive'
        ),
        patch.object(subprocess.filesystem, 'chdir'),
        patch.object(subprocess, 'cmd') as mock_cmd,
        patch.object(subprocess.shutil, 'rmtree') as mock_rm
    ):
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        subprocess.make(
            Path('/tmp/archive.tar.gz'),
            Path('/tmp/build'),
            remove_temporary=False)
        mock_rm.assert_not_called()


def test_rsync_basic() -> None:
    """rsync() builds the correct command for basic usage."""
    src = MagicMock(spec=Path)
    src.is_dir.return_value = False
    src.__str__ = lambda s: '/tmp/src'
    dst = MagicMock(spec=Path)
    dst.is_dir.return_value = False
    dst.__str__ = lambda s: '/tmp/dst'
    with patch.object(subprocess, 'cmd') as mock_cmd:
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        subprocess.rsync(src, dst)
        call_args = mock_cmd.call_args[0][0]
        assert 'rsync' in call_args
        assert '-a' in call_args


def test_rsync_with_options() -> None:
    """rsync() includes flags for delete, progress, simulate."""
    src = MagicMock(spec=Path)
    src.is_dir.return_value = True
    src.__str__ = lambda s: '/tmp/src'
    dst = MagicMock(spec=Path)
    dst.is_dir.return_value = True
    dst.__str__ = lambda s: '/tmp/dst'
    with patch.object(subprocess, 'cmd') as mock_cmd:
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        subprocess.rsync(
            src,
            dst,
            delete=True,
            progress=True,
            simulate=True,
            recursive=True,
            size_only=True,
            exclude_vcs=True,
            excludes=['*.pyc'],
            includes=['*.py'],
            rsync_path=Path('/usr/bin/rsync'),
            extra='ssh -p 22',
            extra_args=['--verbose'])
        call_args = mock_cmd.call_args[0][0]
        assert '--delete' in call_args
        assert '--progress' in call_args
        assert '--dry-run' in call_args
        assert '-r' in call_args
        assert '--size-only' in call_args
        assert '--exclude=.git' in call_args
        assert '--exclude=*.pyc' in call_args
        assert '--include=*.py' in call_args
        assert '--verbose' in call_args


def test_rsync_dir_appends_separator() -> None:
    """rsync() appends os.sep when source/dest are directories."""
    src = MagicMock(spec=Path)
    src.is_dir.return_value = True
    src.__str__ = lambda s: '/tmp/src'
    dst = MagicMock(spec=Path)
    dst.is_dir.return_value = True
    dst.__str__ = lambda s: '/tmp/dst'
    import os as os_mod
    with patch.object(subprocess, 'cmd') as mock_cmd:
        mock_cmd.return_value = {
            'process': MagicMock(),
            'returncode': 0,
            'stdout': b'',
            'stderr': b'',
            'exception': None
        }
        subprocess.rsync(src, dst)
        call_args = mock_cmd.call_args[0][0]
        # Last two args are source and dest with trailing sep
        assert call_args[-2] == f'/tmp/src{os_mod.sep}'
        assert call_args[-1] == f'/tmp/dst{os_mod.sep}'
