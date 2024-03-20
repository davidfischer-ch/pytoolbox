# pylint:disable=too-few-public-methods
from __future__ import annotations

from pytoolbox import module
from pytoolbox.unittest import asserts

not_included_variable = 0  # pylint:disable=invalid-name

_all = module.All(globals())

from pytoolbox import types, validation as _validation  # noqa pylint:disable=wrong-import-position

public_variable = 0    # pylint:disable=invalid-name
_private_variable = 0  # pylint:disable=invalid-name


def public_function():
    pass


class PublicClass(types.MissingType):
    pass


class _PrivateClass(_validation.CleanAttributesMixin):
    pass


asserts.equal(
    set(_all.diff(globals())),
    {'public_variable', 'public_function', 'PublicClass', 'types'})
