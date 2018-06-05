# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import exceptions

from . import base


class TestExceptions(base.TestCase):

    tags = ('exceptions', )

    def test_message_mixin_to_string(self):
        ex = exceptions.MessageMixin(ten=10, dict={}, string='chaîne de caractères')
        ex.message = 'Ten equals {ten} an empty dict {dict} a string is a {string}'
        self.equal('%s' % ex, 'Ten equals 10 an empty dict {} a string is a chaîne de caractères')

    def test_message_mixin_to_string_includes_class_attributes(self):

        class NewError(exceptions.MessageMixin, IOError):
            message = 'The attribute from {my_attr}'
            my_attr = 'class'

        self.equal('%s' % NewError(), 'The attribute from class')
        self.equal('%s' % NewError(my_attr='instance'), 'The attribute from instance')

    def test_message_mixin_to_string_missing_key(self):
        ex = exceptions.MessageMixin('Ten equals {ten} an empty dict {dict} a string is a {string}', ten=10, dict={})
        with self.raises(KeyError):
            '%s' % ex
