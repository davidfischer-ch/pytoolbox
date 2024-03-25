from __future__ import annotations

import pytest
from pytoolbox import exceptions


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


def test_ssh_error_repr() -> None:
    assert repr(exceptions.SSHAgentParsingError(output='A')) == "SSHAgentParsingError(output='A')"
