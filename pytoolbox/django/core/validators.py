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

import copy, re

from django.core import validators
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _

from ... import module

_all = module.All(globals())


class EmptyValidator(validators.RegexValidator):
    regex = r'\S+'
    message = _('This field cannot be blank.')
    code = 'blank'


@deconstructible
class KeysValidator(object):
    """
    A validator designed for HStore to require, even restrict keys.

    Code mostly borrowed from: https://github.com/django/django/blob/master/django/contrib/postgres/validators.py
    """

    messages = {
        'missing_keys': _('Some keys were missing: %(keys)s'),
        'extra_keys': _('Some unknown keys were provided: %(keys)s'),
    }
    strict = False

    def __init__(self, required_keys=None, optional_keys=None, strict=False, messages=None):
        self.required_keys = set(required_keys or [])
        self.optional_keys = set(optional_keys or [])
        if not self.required_keys and not self.optional_keys:
            raise ImproperlyConfigured('You must set at least `required_keys` or `optional_keys`')
        self.strict = strict
        if messages is not None:
            self.messages = copy.copy(self.messages)
            self.messages.update(messages)

    def __call__(self, value):
        keys = set(value.keys())
        if self.required_keys:
            missing_keys = self.required_keys - keys
            if missing_keys:
                raise ValidationError(self.messages['missing_keys'], code='missing_keys',
                                      params={'keys': ', '.join(missing_keys)})
        if self.strict:
            extra_keys = keys - self.required_keys - self.optional_keys
            if extra_keys:
                raise ValidationError(self.messages['extra_keys'], code='extra_keys',
                                      params={'keys': ', '.join(extra_keys)})

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.required_keys == other.required_keys
            and self.optional_keys == other.optional_keys
            and self.messages == other.messages
            and self.strict == other.strict
        )

    def __ne__(self, other):
        return not self == other


class MD5ChecksumValidator(validators.RegexValidator):
    regex = re.compile(r'[0-9a-f]{32}')

__all__ = _all.diff(globals())
