# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

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
