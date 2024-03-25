from __future__ import annotations

from typing import Final
import os

from pytest import raises

from pytoolbox import exceptions, ssh
from pytoolbox.unittest import skip_if_missing

SSH_PRIVATE_KEY: Final[str] = """-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----"""


@skip_if_missing('ssh-agent')
def test_add_fingerprint(tmp_path):
    path = tmp_path / 'signature'
    ssh.add_fingerprint(path, 'github.com')
    assert ' ssh-rsa ' in path.read_text(encoding='utf-8')


@skip_if_missing('ssh-agent')
def test_add_key():
    ssh.stop_agent()
    assert not ssh.is_agent_up()
    try:
        ssh.add_key(SSH_PRIVATE_KEY)
    except exceptions.SSHAgentConnectionError:
        # On some desktop systems SSH agent is kept alive,
        # Se we are not sure if the exception is raised on not
        pass
    with ssh.scoped_agent():
        with raises(exceptions.SSHAgentLoadingKeyError):
            ssh.add_key('biboum')
        ssh.add_key(SSH_PRIVATE_KEY)


@skip_if_missing('ssh-agent')
def test_scoped_agent():
    ssh.stop_agent()
    assert not ssh.is_agent_up()
    with ssh.scoped_agent() as variables:
        pid = variables.pop('SSH_AGENT_PID')
        assert int(pid) > 0
        assert ssh.is_agent_up()
        assert os.environ['SSH_AGENT_PID'] == pid
    assert not ssh.is_agent_up()
    assert 'SSH_AGENT_PID' not in os.environ


@skip_if_missing('ssh-agent')
def test_start_agent():
    ssh.stop_agent()
    assert not ssh.is_agent_up()
    variables = ssh.start_agent()
    sock_path = variables.pop('SSH_AUTH_SOCK')
    assert int(variables.pop('SSH_AGENT_PID')) > 0
    assert os.path.exists(sock_path), sock_path
    assert not variables
    assert ssh.stop_agent()


@skip_if_missing('ssh-agent')
def test_stop_agent():
    ssh.stop_agent()
    assert not ssh.is_agent_up()
    assert not ssh.stop_agent()
    ssh.start_agent()
    assert ssh.stop_agent()
    assert 'SSH_AGENT_PID' not in os.environ
    assert not ssh.stop_agent()
