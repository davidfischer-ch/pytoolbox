#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import uuid
from ming.schema import FancySchemaItem, String, Invalid
from pyutils.pyutils import valid_filename, valid_email, valid_secret, valid_uuid


class Filename(String):

    def __init__(self, url_friendly, **kwargs):
        self.url_friendly = url_friendly
        String.__init__(self, **kwargs)

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if self.url_friendly:
            value = value.replace(' ', '_')
        if not valid_filename(value):
            raise Invalid('%s is not a valid file-name' % value, value, None)
        return value


class Email(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if not valid_email(value):
            raise Invalid('%s is not a valid e-mail address' % value, value, None)
        return value


class OneOf(FancySchemaItem):

    def __init__(self, type, *options, **kwargs):
        self.type = type
        self.options = options
        FancySchemaItem.__init__(self, **kwargs)

    def _validate(self, value, **kw):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if value not in self.options:
            raise Invalid('%s is not in %r' % (value, (self.options,)), value, None)
        return value


class Secret(String):

    @staticmethod
    def is_hashed(value):
        return value is not None and str(value).startswith('$pbkdf2-sha512$')

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if not Secret.is_hashed(value) and not valid_secret(value, True):
            raise Invalid('%s is not safe (8+ characters, upper/lower + numbers eg. StrongP6s)' %
                          value, value, None)
        return value


class UniqueId(String):

    def if_missing(self):
        u'''Provides a UUID string as default.'''
        return str(uuid.uuid4())

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if not valid_uuid(value, objectid_allowed=False, none_allowed=False):
            raise Invalid('%s is not a valid UUID string' % value, value, None)
        return value


class Uri(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('%s is not a %s' % (value, self.type), value, None)
        if False:  # FIXME TODO
            raise Invalid('%s is not a valid URI' % value, value, None)
        return value
