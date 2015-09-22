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

import functools, re

import voluptuous

from . import module
from .validation import valid_email

_all = module.All(globals())


# Errors

class PasswordInvalid(voluptuous.Invalid):
    """Incorrect password"""


class VersionInvalid(voluptuous.Invalid):
    """Incorrect version number"""


# Validators

@voluptuous.message('Incorrect e-mail address')
def Email(value):
    value = str(value)
    if not valid_email(value):
        raise ValueError
    return value


@voluptuous.message('Incorrect list of e-mail addresses')
def EmailSet(values):
    emails = set()
    for value in values or []:
        email = str(value)
        if not valid_email(email):
            raise ValueError
        emails.add(email)
    return emails


@voluptuous.message('Incorrect git commit hash')
def GitCommitHash(value):
    if re.match(r'^[0-9a-f]{40}$', value):
        return value
    raise ValueError


def Password(length=16, msg=None):

    @functools.wraps(Password)
    def f(value):
        value = str(value)
        if len(value) < length:
            raise PasswordInvalid(msg or 'Incorrect password')
    return f


@voluptuous.message('Incorrect percentage')
def Percent(value):
    return voluptuous.Range(min=1, max=100)(value)


@voluptuous.message('Incorrect SHA-256 checksum')
def SHA256(value):
    if re.match(r'^[0-9a-f]{64}$', value):
        return value
    raise ValueError


def Version(digits=4, msg=None):
    assert digits in range(1, 5)  # 1-4 not 5

    @functools.wraps(Version)
    def f(value):
        if re.match(r'^[0-9]+(\.[0-9]+){%d}\.[a-z0-9]+$' % (digits - 2), value):
            return value
        raise VersionInvalid(msg or 'Incorrect version number')
    return f

__all__ = _all.diff(globals())
