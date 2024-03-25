from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import contextlib
import logging
import os
import stat
import tempfile

from . import exceptions, humanize, subprocess
from .subprocess import CallArgType

log = logging.getLogger(__name__)

__all__ = ['blame', 'clone_or_pull', 'create_tag', 'get_ref', 'get_tags', 'scoped_ssh_key']


def blame(file_path: Path) -> list[str]:
    lines = subprocess.cmd(
        ['git', 'blame', file_path],
        cwd=file_path.parent)['stdout'].decode('utf-8')
    return [line for line in lines.split(os.linesep) if line]


def clone_or_pull(
    directory: Path,
    url: str,
    *,
    bare: bool = False,
    clone_depth: int | None = None,
    reset: bool = True
) -> None:
    if directory.exists():
        if reset and not bare:
            subprocess.cmd(['git', 'reset', '--hard'], cwd=directory)
        subprocess.cmd(['git', 'fetch' if bare else 'pull'], cwd=directory)
    else:
        command: list[CallArgType] = ['git', 'clone']
        if bare:
            command.append('--bare')
        if clone_depth:
            command.extend(['--depth', clone_depth])
        command.extend([url, directory])
        subprocess.cmd(command)


def create_tag(directory: Path, name: str) -> None:
    try:
        subprocess.cmd(['git', 'tag', name], cwd=directory)
    except exceptions.CalledProcessError as ex:
        if name in get_tags(directory):
            # Parsing output is not robust since it can be in French, English, ...
            raise exceptions.DuplicateGitTagError(tag=name) from ex
        raise


def get_ref(directory: Path | None = None, *, ci_vars: bool = True, kind: str = 'branch') -> str:
    """
    Return the Git reference looking first at CI context, then using Git CLI.

    This function will return either:

    * The content of the environment variable CI_COMMIT_REF_NAME when available (GitLab CI/CD)
    * The git branch reference to point to the branch when running locally (via git CLI)
    """
    if ci_vars and (ref := os.getenv('CI_COMMIT_REF_NAME')):
        log.debug(f'Detected Git ref from GitLab CI context is {ref}')
    else:
        extra = {'branch': ['--abbrev-ref'], 'commit': []}[kind]
        ref = subprocess.cmd(
            ['git', 'rev-parse', *extra, 'HEAD'],
            cwd=directory,
            fail=False,
            log=log)['stdout'].decode('utf-8').strip()
        log.debug(f'Detected Git ref from directory {directory!r} of kind {kind} is {ref}')
    if not ref:
        raise exceptions.GitReferenceError()
    return ref


def get_tags(directory: Path, *, ref: str | None = None) -> list[str]:
    """Return tags from local copy. Optionally restrict to tags related to given `ref`."""
    extra = [] if ref is None else ['--points-at', ref]
    tags = subprocess.cmd(['git', 'tag', *extra], cwd=directory)['stdout'].decode('utf-8')
    return sorted((t for t in tags.split(os.linesep) if t), key=humanize.natural_int_key)


@contextlib.contextmanager
def scoped_ssh_key(
    directory: Path,
    content: str,
    *,
    options: tuple[str] = tuple(),  # type: ignore[assignment]
) -> Iterator[str]:
    """Load an SSH key (content is the private key)."""
    with tempfile.NamedTemporaryFile('w') as key_file:
        os.chmod(key_file.name, stat.S_IRUSR)
        key_file.write(content + os.linesep)
        key_file.flush()
        try:
            log.debug(f'Set identity "...{content[100:120]}..."')
            options_str = ' '.join(f'-o {o}' for o in options) if options else ''
            ssh_cmd = f'ssh -F /dev/null -i {key_file.name} -o IdentitiesOnly=yes {options_str}'
            subprocess.cmd(
                ['git', 'config', 'core.sshCommand', ssh_cmd],
                cwd=directory,
                env=os.environ)
        except exceptions.CalledProcessError:  # pylint:disable=try-except-raise
            raise
        else:
            yield key_file.name
        finally:
            log.debug(f'Unset identity "...{content[100:120]}..."')
            subprocess.cmd(
                ['git', 'config', '--unset', 'core.sshCommand'],
                cwd=directory,
                env=os.environ)
