# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pyutils Project.
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
# Retrieved from https://github.com/davidfischer-ch/pyutils.git

from __future__ import absolute_import

import uuid
from ming.schema import FancySchemaItem, String, Invalid
from ..validation import valid_filename, valid_email, valid_secret, valid_uuid


class Filename(String):

    def __init__(self, url_friendly, **kwargs):
        self.url_friendly = url_friendly
        String.__init__(self, **kwargs)

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if self.url_friendly:
            value = value.replace(u' ', u'_')
        if not valid_filename(value):
            raise Invalid(u'{0} is not a valid file-name'.format(value), value, None)
        return value


class Email(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if not valid_email(value):
            raise Invalid(u'{0} is not a valid e-mail address'.format(value), value, None)
        return value


class OneOf(FancySchemaItem):

    def __init__(self, type, *options, **kwargs):
        self.type = type
        self.options = options
        FancySchemaItem.__init__(self, **kwargs)

    def _validate(self, value, **kw):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if value not in self.options:
            raise Invalid(u'{0} is not in {1}'.format(value, (self.options,)), value, None)
        return value


class Secret(String):

    @staticmethod
    def is_hashed(value):
        return value is not None and unicode(value).startswith(u'$pbkdf2-sha512$')

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if not Secret.is_hashed(value) and not valid_secret(value, True):
            raise Invalid(u'{0} is not safe (8+ characters, upper/lower + numbers eg. StrongP6s)'
                          .format(value), value, None)
        return value


class UniqueId(String):

    def if_missing(self):
        u'''Provides a UUID string as default.'''
        return unicode(uuid.uuid4())

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if not valid_uuid(value, objectid_allowed=False, none_allowed=False):
            raise Invalid(u'{0} is not a valid UUID string'.format(value), value, None)
        return value


class Uri(String):

    def _validate(self, value, **kwargs):
        if not isinstance(value, self.type):
            raise Invalid(u'{0} is not a {1}'.format(value, self.type), value, None)
        if False:  # FIXME TODO
            raise Invalid(u'{0} is not a valid URI'.format(value), value, None)
        return value
