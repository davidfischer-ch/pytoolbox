from __future__ import annotations

from pathlib import Path
from unittest.mock import patch as M
from typing import Final
import os
import tempfile

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
    '7.1.8-beta'
]


def test_blame(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
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
    print(pytoolbox_git)
    pytest.skip('Not implemented.')


def test_create_tag(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    with raises(exceptions.DuplicateGitTagError):
        git.create_tag(pytoolbox_git, '14.7.0')
    git.create_tag(pytoolbox_git, 'z1.0')
    git.create_tag(pytoolbox_git, 'z2.0')
    tags = git.get_tags(pytoolbox_git)
    assert 'z1.0' in tags and 'z2.0' in tags


def test_get_ref(pytoolbox_git: Path) -> None:
    get_ref = git.get_ref
    with M.dict(os.environ, {}, clear=True):
        assert get_ref(pytoolbox_git, kind='branch') == 'main'
        assert get_ref(pytoolbox_git, kind='commit') == '4863c99a97fe358caa24e48b5c477b852b5a6721'
        with raises(exceptions.GitReferenceError):
            get_ref(tempfile.gettempdir())


def test_get_ref_from_gitlab_ci(pytoolbox_git: Path) -> None:
    get_ref = git.get_ref
    with M.dict(os.environ, {'CI_COMMIT_REF_NAME': 'toto'}, clear=True):
        assert get_ref(pytoolbox_git, kind='branch') == 'toto'
        assert get_ref(pytoolbox_git, kind='commit') == 'toto'
        assert get_ref(pytoolbox_git, kind='branch', ci_vars=False) != 'toto'
        assert get_ref(pytoolbox_git, kind='commit', ci_vars=False) != 'toto'


def test_get_tags(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    tags = git.get_tags(pytoolbox_git)
    assert tags[:len(EXPECTED_PYTOOLBOX_TAGS)] == EXPECTED_PYTOOLBOX_TAGS
    assert '' not in tags  # Known potential bug


def test_get_tags_with_ref(pytoolbox_git: Path) -> None:  # pylint:disable=redefined-outer-name
    tags = git.get_tags
    assert tags(pytoolbox_git, ref='4863c99a97fe358caa24e48b5c477b852b5a6721') == ['14.7.0']
    assert tags(pytoolbox_git, ref='0b87f1b5cf21e18205e334652167c1055d0b4c13') == []
    git.create_tag(pytoolbox_git, 'some-tag')
    git.create_tag(pytoolbox_git, 'other-tag')
    assert tags(pytoolbox_git, ref='HEAD') == ['14.7.0', 'other-tag', 'some-tag']


def test_scoped_ssh_key() -> None:
    with M('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': None, 'stderr': None, 'returncode': 0}
        with git.scoped_ssh_key('.', 'key-data') as name:
            subprocess.cmd(['git', 'push', 'somewhere'])

        assert [args for args, kwargs in cmd.call_args_list] == [
            ([
                'git', 'config', 'core.sshCommand',
                f'ssh -F /dev/null -i {name} -o IdentitiesOnly=yes '
            ], ),
            (['git', 'push', 'somewhere'], ),
            (['git', 'config', '--unset', 'core.sshCommand'], )
        ]


def test_scoped_ssh_key_with_options() -> None:
    with M('pytoolbox.subprocess.cmd') as cmd:
        cmd.return_value = {'stdout': None, 'stderr': None, 'returncode': 0}
        with git.scoped_ssh_key('.', 'key-data', options=['StrictHostKeyChecking=no']) as name:
            subprocess.cmd(['git', 'push', 'somewhere'])
            assert Path(name).read_text(encoding='utf-8') == 'key-data\n'

        assert not Path(name).exists()
        assert [args for args, kwargs in cmd.call_args_list] == [
            ([
                'git', 'config', 'core.sshCommand',
                f'ssh -F /dev/null -i {name} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no'
            ], ),
            (['git', 'push', 'somewhere'], ),
            (['git', 'config', '--unset', 'core.sshCommand'], )
        ]
