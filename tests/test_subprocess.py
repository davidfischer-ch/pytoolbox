from __future__ import annotations

from unittest import mock

import pytest
from pytoolbox import regex, subprocess
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


def test_cmd() -> None:
    log = mock.Mock()
    subprocess.cmd(['echo', 'it seem to work'], log=log)
    assert subprocess.cmd('cat missing_file', fail=False, log=log)['returncode'] == 1
    assert log.call_args_list == [
        mock.call("Execute echo 'it seem to work'"),
        mock.call('Execute cat missing_file'),
        mock.call('Attempt 1 out of 1: Failed')
    ]
    assert subprocess.cmd('my.funny.missing.script.sh', fail=False)['stderr'] != ''
    result = subprocess.cmd(f'cat {__file__}')
    # There are at least 30 lines in this source file !
    assert len(result['stdout'].splitlines()) > 30


def test_cmd_missing_binary() -> None:
    assert subprocess.cmd('hfuejnvwqkdivengz', fail=False)['returncode'] == 2


def test_retry_first_try() -> None:
    log = mock.Mock()
    subprocess.cmd('ls', log=log, tries=5, delay_min=1, delay_max=1)
    log.assert_called_once_with('Execute ls')


def test_retry_missing_binary_no_retry() -> None:
    log = mock.Mock()
    with pytest.raises(OSError):
        subprocess.cmd('hfuejnvwqkdivengz', log=log, tries=5)
    validate_list(log.call_args_list, [
        r"call\('Execute hfuejnvwqkdivengz'\)",
        r'call\(FileNotFoundError.*\)'
    ])


def test_retry_no_success() -> None:
    log = mock.Mock()
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
