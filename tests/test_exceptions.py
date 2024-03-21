from __future__ import annotations

import pytest
from pytoolbox import exceptions


def test_message_mixin_to_string() -> None:
    ex = exceptions.MessageMixin(ten=10, dict={}, string='chaîne de caractères')
    ex.message = 'Ten equals {ten} an empty dict {dict} a string is a {string}'
    assert str(ex) == 'Ten equals 10 an empty dict {} a string is a chaîne de caractères'


def test_message_mixin_to_string_includes_class_attributes() -> None:

    class NewError(exceptions.MessageMixin, IOError):
        message = 'The attribute from {my_attr}'
        my_attr = 'class'

    assert str(NewError()) == 'The attribute from class'
    assert str(NewError(my_attr='instance')) == 'The attribute from instance'


def test_message_mixin_to_string_missing_key() -> None:
    ex = exceptions.MessageMixin(
        'Ten equals {ten} an empty dict {dict} a string is a {string}',
        ten=10,
        dict={})
    with pytest.raises(KeyError):
        str(ex)
