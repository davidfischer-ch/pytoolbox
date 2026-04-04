"""Tests for the exceptions module."""

from __future__ import annotations

import pytest
from pytest import raises

from pytoolbox import exceptions


def test_message_mixin_validation() -> None:
    """MessageMixin raises AttributeError when required attrs are missing."""

    class NewError(exceptions.MessageMixin, Exception):
        """Test error class for MessageMixin validation."""

        attrs: tuple[str, ...] = ('b', 'c')
        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    with raises(AttributeError, match=r'is missing attributes or properties: b, c'):
        # pylint:disable=pointless-exception-statement
        NewError(ten=10, dict={}, string='chaîne de caractères')


def test_message_mixin_str() -> None:
    """MessageMixin renders message template with provided kwargs."""

    class NewError(exceptions.MessageMixin, Exception):
        """Test error class for MessageMixin string rendering."""

        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    exc = NewError(ten=10, dict={}, string='chaîne de caractères')
    assert str(exc) == 'Ten equals 10 an empty dict {} a string is a chaîne de caractères'


def test_message_mixin_str_includes_class_attributes() -> None:
    """MessageMixin uses both class attributes and instance kwargs in message."""

    class NewError(exceptions.MessageMixin, IOError):
        """Test error class for attribute resolution."""

        message: str = 'The attribute from {my_attr}'
        my_attr: str = 'class'

    assert str(NewError()) == 'The attribute from class'
    assert str(NewError(my_attr='instance')) == 'The attribute from instance'


def test_message_mixin_str_missing_key() -> None:
    """MessageMixin raises KeyError when message template key is missing."""

    class NewError(exceptions.MessageMixin, Exception):
        """Test error class for missing key behavior."""

        message: str = 'Ten equals {ten} an empty dict {dict} a string is a {string}'

    exc = NewError(ten=10, dict={})
    with pytest.raises(KeyError):
        str(exc)


def test_called_process_error_repr_and_str() -> None:
    """CalledProcessError repr and str format correctly with truncated cmd."""
    exc = exceptions.CalledProcessError(
        cmd=['find', '-maxdepth=2', '-type=f', '-gid=0', '-uid=0', '/'],
        returncode=1,
        stdout=b'',
        stderr=b'Error something wrong happened.',
    )

    assert repr(exc) == (
        "CalledProcessError(cmd_short=['find', '-maxdepth=2', '-type=f', '-gid=0', '(…)'], "
        'returncode=1)'
    )
    assert str(exc) == (
        "Process ['find', '-maxdepth=2', '-type=f', '-gid=0', '(…)'] failed with return code 1"
    )


def test_ssh_error_repr() -> None:
    """SSHAgentParsingError repr includes the output attribute."""
    assert repr(exceptions.SSHAgentParsingError(output='A')) == "SSHAgentParsingError(output='A')"
