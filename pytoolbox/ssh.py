from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Final
import contextlib
import logging
import os
import re
import signal
import stat
import tempfile

from . import exceptions, subprocess

__all__ = [
    'AGENT_START_REGEX',
    'add_fingerprint',
    'add_key',
    'is_agent_up',
    'scoped_agent',
    'start_agent',
    'stop_agent',
    'ssh'
]

log = logging.getLogger(__name__)

AGENT_START_REGEX: Final[re.Pattern] = re.compile(
    r'SSH_AUTH_SOCK=(?P<SSH_AUTH_SOCK>[^;]+).*'
    r'SSH_AGENT_PID=(?P<SSH_AGENT_PID>\d+)',
    re.MULTILINE | re.DOTALL)


def add_fingerprint(path: Path, host: str) -> None:
    """Scan an host's SSH fingerprint and add it to the list of known hosts."""
    log.info(f'Adding SSH fingerprint of host {host}')
    keys: bytes = subprocess.cmd(['ssh-keyscan', '-H', host])['stdout']
    with path.open('ab') as key_file:
        key_file.write(keys)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def add_key(content: str) -> None:
    """Load an SSH key (content is the private key)."""
    with tempfile.NamedTemporaryFile('w') as key_file:
        key_file.write(content + os.linesep)
        key_file.flush()
        try:
            output: bytes = subprocess.cmd(['ssh-add', key_file.name], env=os.environ)['stderr']
        except exceptions.CalledProcessError as ex:
            if b'Could not open' in ex.stderr:
                raise exceptions.SSHAgentConnectionError()
            if b'Error loading key' in ex.stderr:
                raise exceptions.SSHAgentLoadingKeyError()
            raise
        log.debug(output.decode('utf-8'))


def is_agent_up() -> bool:
    """Return True if an SSH agent is up and running."""
    if (pid := os.environ.get('SSH_AGENT_PID')) is None:
        return False
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    return True


@contextlib.contextmanager
def scoped_agent() -> Iterator[dict]:
    """
    Context manager providing a temporary SSH agent.
    Yields related environment variables.
    """
    variables = start_agent()
    try:
        yield variables
    finally:
        stop_agent()


def start_agent() -> dict:
    """
    Start an SSH agent in the background.
    Export related environment variables.
    """
    output: str = subprocess.cmd(['ssh-agent', '-s'])['stdout'].decode('utf-8')
    if (match := AGENT_START_REGEX.search(output)) is None:
        raise exceptions.SSHAgentParsingError(output=output)
    variables = match.groupdict()
    os.environ.update(variables)
    return variables


def stop_agent() -> bool:
    """
    Stop the SSH agent if one is found.
    Drop related environment variables.
    """
    if (pid := os.environ.get('SSH_AGENT_PID')) is None:
        return False
    try:
        os.kill(int(pid), signal.SIGTERM)
    except ProcessLookupError:
        pass  # Process not found
    os.environ.pop('SSH_AGENT_PID')
    os.environ.pop('SSH_AUTH_SOCK')
    return True


def ssh(
    host: str,
    identity_file: Path | None = None,
    remote_cmd: str | None = None,
    **kwargs
) -> dict:
    command = ['ssh']
    if identity_file is not None:
        command.extend(['-i', identity_file])
    command.append(host)
    if remote_cmd is not None:
        command.extend(['-n', remote_cmd])
    return subprocess.cmd([c for c in command if c], **kwargs)
