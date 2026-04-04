from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Final
from unittest.mock import patch

import pytest
from pytest import raises

from pytoolbox import exceptions, git, subprocess

EXPECTED_PYTOOLBOX_TAGS: Final[list[str]] = [
    '5.6.3-beta',
    '6.2.4-beta',
    '6.3.0-beta',
    '6.4.1-beta',
    '6.5.7-beta',
    '6.6.1-beta',
    '7.0.0-beta',
    '7.1.8-beta',
]


def test_blame(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    """blame() returns git blame output with commit, author, date, and line."""
    f = 'David Fischer'
    assert git.blame(pytoolbox_git / 'AUTHORS.md') == [
        f'f6fcb1e7 AUTHORS.md ({f} 2023-06-08 00:03:14 +0200  1) # Main Developers',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  2) ',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  3) * {f} @davidfischer-ch',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  4) ',
        f'f6fcb1e7 AUTHORS.md ({f} 2023-06-08 00:03:14 +0200  5) # Contributors',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  6) ',
        f'a99773f5 AUTHORS.md ({f} 2024-03-20 14:13:13 +0100  7) * Abdulhadi Mohamed @aa6moham',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  8) * Dimitri Racordon @kyouko-taiga',
        f'2d601050 AUTHORS    ({f} 2014-03-29 08:31:38 +0100  9) * Guillaume Martres @smarter',
        f'a99773f5 AUTHORS.md ({f} 2024-03-20 14:13:13 +0100 10) * Julius Milan @juliusmilan',
        f'a99773f5 AUTHORS.md ({f} 2024-03-20 14:13:13 +0100 11) * Torbjörn Einarsson @tobbee',
    ]


def test_clone_or_pull(pytoolbox_git: Path) -> None:
    """clone_or_pull() clones or updates a git repository."""
    print(pytoolbox_git)
    pytest.skip('Not implemented.')


def test_create_tag(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    """create_tag() creates a new git tag and raises for duplicates."""
    with raises(exceptions.DuplicateGitTagError):
        git.create_tag(pytoolbox_git, '14.7.0')
    git.create_tag(pytoolbox_git, 'z1.0')
    git.create_tag(pytoolbox_git, 'z2.0')
    tags = git.get_tags(pytoolbox_git)
    assert 'z1.0' in tags and 'z2.0' in tags


def test_get_ref(pytoolbox_git: Path) -> None:
    """get_ref() returns the current branch name or commit hash."""
    get_ref = git.get_ref
    with patch.dict(os.environ, {}, clear=True):
        assert get_ref(pytoolbox_git, kind='branch') == 'main'
        assert get_ref(pytoolbox_git, kind='commit') == '4863c99a97fe358caa24e48b5c477b852b5a6721'
        with raises(exceptions.GitReferenceError):
            get_ref(tempfile.gettempdir())


def test_get_ref_from_gitlab_ci(pytoolbox_git: Path) -> None:
    """get_ref() returns CI variable when running in GitLab CI."""
    get_ref = git.get_ref
    with patch.dict(os.environ, {'CI_COMMIT_REF_NAME': 'toto'}, clear=True):
        assert get_ref(pytoolbox_git, kind='branch') == 'toto'
        assert get_ref(pytoolbox_git, kind='commit') == 'toto'
        assert get_ref(pytoolbox_git, kind='branch', ci_vars=False) != 'toto'
        assert get_ref(pytoolbox_git, kind='commit', ci_vars=False) != 'toto'


def test_get_tags(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    """get_tags() returns list of git tags in reverse chronological order."""
    tags = git.get_tags(pytoolbox_git)
    assert tags[: len(EXPECTED_PYTOOLBOX_TAGS)] == EXPECTED_PYTOOLBOX_TAGS
    assert '' not in tags  # Known potential bug


def test_get_tags_with_ref(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    """get_tags() with ref parameter returns tags reachable from that ref."""
    tags = git.get_tags
    assert tags(pytoolbox_git, ref='4863c99a97fe358caa24e48b5c477b852b5a6721') == ['14.7.0']
    assert tags(pytoolbox_git, ref='0b87f1b5cf21e18205e334652167c1055d0b4c13') == []
    git.create_tag(pytoolbox_git, 'some-tag')
    git.create_tag(pytoolbox_git, 'other-tag')
    assert tags(pytoolbox_git, ref='HEAD') == ['14.7.0', 'other-tag', 'some-tag']


def test_scoped_ssh_key() -> None:
    """scoped_ssh_key() temporarily configures git to use an SSH key."""
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': None, 'stderr': None, 'returncode': 0}
        with git.scoped_ssh_key('.', 'key-data') as name:
            subprocess.cmd(['git', 'push', 'somewhere'])

        assert [args for args, kwargs in cmd.call_args_list] == [
            (
                [
                    'git',
                    'config',
                    'core.sshCommand',
                    f'ssh -F /dev/null -i {name} -o IdentitiesOnly=yes ',
                ],
            ),
            (['git', 'push', 'somewhere'],),
            (['git', 'config', '--unset', 'core.sshCommand'],),
        ]


def test_scoped_ssh_key_with_options() -> None:
    """scoped_ssh_key() passes additional SSH options to git."""
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': None, 'stderr': None, 'returncode': 0}
        with git.scoped_ssh_key(
            Path('.'),
            'key-data',
            options=['StrictHostKeyChecking=no'],
        ) as name:
            subprocess.cmd(['git', 'push', 'somewhere'])
            assert Path(name).read_text(encoding='utf-8') == 'key-data\n'

        assert not Path(name).exists()
        assert [args for args, kwargs in cmd.call_args_list] == [
            (
                [
                    'git',
                    'config',
                    'core.sshCommand',
                    f'ssh -F /dev/null -i {name} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no',
                ],
            ),
            (['git', 'push', 'somewhere'],),
            (['git', 'config', '--unset', 'core.sshCommand'],),
        ]


def test_scoped_ssh_key_options_with_spaces() -> None:
    """Options with spaces or shell metacharacters must be quoted."""
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': None, 'stderr': None, 'returncode': 0}
        with git.scoped_ssh_key(
            Path('.'),
            'key-data',
            options=['ProxyCommand ssh -W %h:%p jump-host'],
        ):
            config_call_args = cmd.call_args_list[0][0][0]
            ssh_cmd = config_call_args[3]
            assert "-o 'ProxyCommand ssh -W %h:%p jump-host'" in ssh_cmd


def _make_called_process_error(msg='failed'):  # pylint:disable=unused-argument
    """Create a CalledProcessError with required attributes."""
    return exceptions.CalledProcessError(
        cmd=['git', 'test'],
        returncode=1,
        stdout=b'',
        stderr=b'',
    )


def test_scoped_ssh_key_config_fails() -> None:
    """scoped_ssh_key re-raises CalledProcessError from git config."""
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.side_effect = _make_called_process_error()
        with pytest.raises(exceptions.CalledProcessError):
            with git.scoped_ssh_key(Path('.'), 'x' * 200):
                pass  # pragma: no cover


def test_clone_or_pull_existing_directory(tmp_path: Path) -> None:
    """clone_or_pull fetches and resets when directory already exists."""
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}
        git.clone_or_pull(repo_dir, 'https://example.com/repo.git')
    calls = [args[0][0] for args in cmd.call_args_list]
    assert calls[0] == ['git', 'reset', '--hard']
    assert calls[1] == ['git', 'pull']


def test_clone_or_pull_existing_bare(tmp_path: Path) -> None:
    """clone_or_pull with bare=True fetches without reset."""
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}
        git.clone_or_pull(repo_dir, 'https://example.com/repo.git', bare=True)
    calls = [args[0][0] for args in cmd.call_args_list]
    assert len(calls) == 1
    assert calls[0] == ['git', 'fetch']


def test_clone_or_pull_existing_no_reset(tmp_path: Path) -> None:
    """clone_or_pull with reset=False skips git reset."""
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}
        git.clone_or_pull(
            repo_dir,
            'https://example.com/repo.git',
            reset=False,
        )
    calls = [args[0][0] for args in cmd.call_args_list]
    assert len(calls) == 1
    assert calls[0] == ['git', 'pull']


def test_clone_or_pull_new_directory(tmp_path: Path) -> None:
    """clone_or_pull clones when directory does not exist."""
    repo_dir = tmp_path / 'new_repo'
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}
        git.clone_or_pull(
            repo_dir,
            'https://example.com/repo.git',
            clone_depth=1,
        )
    call_args = cmd.call_args_list[0][0][0]
    assert call_args[:2] == ['git', 'clone']
    assert '--depth' in call_args
    assert 1 in call_args


def test_clone_or_pull_new_bare(tmp_path: Path) -> None:
    """clone_or_pull clones with --bare flag when bare=True."""
    repo_dir = tmp_path / 'new_repo'
    with patch('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': b'', 'stderr': b'', 'returncode': 0}
        git.clone_or_pull(
            repo_dir,
            'https://example.com/repo.git',
            bare=True,
        )
    call_args = cmd.call_args_list[0][0][0]
    assert '--bare' in call_args


def test_create_tag_unknown_error(tmp_path: Path) -> None:
    """create_tag re-raises CalledProcessError when tag is not a duplicate."""
    with (
        patch('pytoolbox.subprocess.cmd') as cmd,
        patch('pytoolbox.git.get_tags', return_value=[]),
    ):
        cmd.side_effect = _make_called_process_error()
        with pytest.raises(exceptions.CalledProcessError):
            git.create_tag(tmp_path, 'v1.0')
