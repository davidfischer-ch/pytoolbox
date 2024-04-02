from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest
from pytoolbox import logging, regex, subprocess
from pytoolbox.validation import validate_list


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
    assert result['stderr'] == b'cat: missing_file: No such file or directory\n'
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
