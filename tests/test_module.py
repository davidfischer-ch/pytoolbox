# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module
from pytoolbox.unittest import asserts

not_included_variable = 0

_all = module.All(globals())

from pytoolbox import types, validation as _validation

public_variable = 0
_private_variable = 0


def public_function():
    pass


class PublicClass(types.MissingType):
    pass


class _PrivateClass(_validation.CleanAttributesMixin):
    pass


asserts.equal(_all.diff(globals(), to_type=set), {'public_variable', 'public_function', 'PublicClass', 'types'})
