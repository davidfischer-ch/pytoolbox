from __future__ import annotations

import pytest
from pytest import raises
from pytoolbox import exceptions


def test_message_mixin_validation() -> None:

    class NewError(exceptions.MessageMixin, Exception):
        attrs: tuple[str, ...] = ('b', 'c')
        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    with raises(AttributeError, match=r"is missing attributes or properties: b, c"):
        NewError(ten=10, dict={}, string='chaîne de caractères')


def test_message_mixin_str() -> None:

    class NewError(exceptions.MessageMixin, Exception):
        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    ex = NewError(ten=10, dict={}, string='chaîne de caractères')
    assert str(ex) == 'Ten equals 10 an empty dict {} a string is a chaîne de caractères'


def test_message_mixin_str_includes_class_attributes() -> None:

    class NewError(exceptions.MessageMixin, IOError):
        message: str = 'The attribute from {my_attr}'
        my_attr: str = 'class'

    assert str(NewError()) == 'The attribute from class'
    assert str(NewError(my_attr='instance')) == 'The attribute from instance'


def test_message_mixin_str_missing_key() -> None:

    class NewError(exceptions.MessageMixin, Exception):
        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    ex = NewError(ten=10, dict={})
    with pytest.raises(KeyError):
        str(ex)


def test_called_process_error_repr_and_str() -> None:
    ex = exceptions.CalledProcessError(
        cmd=['find', '-maxdepth=2', '-type=f', '-gid=0', '-uid=0', '/'],
        returncode=1,
        stdout=b'',
        stderr=b'Error something wrong happened.')

    assert repr(ex) == (
        "CalledProcessError(cmd_short=['find', '-maxdepth=2', '-type=f', '-gid=0', '(…)'], "
        "returncode=1)")
    assert str(ex) == (
        "Process ['find', '-maxdepth=2', '-type=f', '-gid=0', '(…)'] failed with return code 1")


def test_ssh_error_repr() -> None:
    assert repr(exceptions.SSHAgentParsingError(output='A')) == "SSHAgentParsingError(output='A')"
