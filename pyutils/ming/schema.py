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
from ming.schema import String, Invalid
from pyutils.pyutils import valid_filename, valid_mail, valid_secret, valid_uuid


class Filename(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('mail is not a %s' % self.type, value, None)
        value = value.replace(' ', '_')
        if not valid_filename(value):
            raise Invalid('filename is not a valid file-name', value, None)
        return value


class Mail(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('mail is not a %s' % self.type, value, None)
        if not valid_mail(value):
            raise Invalid('mail is not a valid email address', value, None)
        return value


class MediaStatus(String):

    STATUS = ('PENDING', 'READY', 'PUBLISHED', 'DELETED')

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('status is not a %s' % self.type, value, None)
        if value not in MediaStatus.STATUS:
            raise Invalid('status is not in %s' % (MediaStatus.STATUS,), value, None)
        return value


class Secret(String):

    @staticmethod
    def is_hashed(value):
        return value is not None and str(value).startswith('$pbkdf2-sha512$')

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('secret is not a %s' % self.type, value, None)
        if not Secret.is_hashed(value) and not valid_secret(value, True):
            raise Invalid('secret is not safe (8+ characters, upper/lower + numbers eg. StrongP6s)', value, None)
        return value


class UniqueId(String):

    def if_missing(self):
        u'''Provides a UUID string as default.'''
        return str(uuid.uuid4())

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('_id is not a %s' % self.type, value, None)
        if not valid_uuid(value, objectid_allowed=False, none_allowed=False):
            raise Invalid('_id is not a valid UUID string', value, None)
        return value


class Uri(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid('uri is not a %s' % self.type, value, None)
        if False:  # FIXME TODO
            raise Invalid('uri is not a valid URI', value, None)
        return value
