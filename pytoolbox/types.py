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

import collections, itertools

from . import module
from .encoding import binary_type, string_types

_all = module.All(globals())


def get_slots(obj):
    """Return a set with the `__slots__` of the `obj` including all parent classes `__slots__`."""
    return set(itertools.chain.from_iterable(getattr(cls, '__slots__', ()) for cls in obj.__class__.__mro__))


def isiterable(obj):
    """
    Return ``True`` if the object is an iterable, but ``False`` for :class:`str` or :class:`bytes`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> for obj in 'text', b'binary', u'unicode', 42:
    ...     asserts.false(isiterable(obj), obj)
    >>> for obj in [], (), set(), {}.iteritems():
    ...     asserts.true(isiterable(obj), obj)
    """
    return isinstance(obj, collections.abc.Iterable) and not isinstance(obj, (binary_type, string_types))


class MissingType(object):

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __nonzero__(self):
        return False

    def __repr__(self):
        return 'Missing'


Missing = MissingType()

__all__ = _all.diff(globals())
