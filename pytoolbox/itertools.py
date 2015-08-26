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

import itertools

from . import module
from .types import isiterable

_all = module.All(globals())


def chain(*args, **kwargs):
    """
    Chain the arguments, handle non iterable arguments gracefully.

    * Set `callback` to a function checking if the argument is iterable, defaults to :func:`isiterable`.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.list_equal(list(chain(1, 2, '3', [4, 5], {6: 7})), [1, 2, '3', 4, 5, 6])
    >>> list(chain(1, 2, '3', callback=lambda a: True))
    Traceback (most recent call last):
        ...
    TypeError: 'int' object is not iterable
    """
    callback = kwargs.pop('callback', isiterable)
    if kwargs:
        raise TypeError('Invalid arguments for {0} {1}'.format(chain, kwargs.iterkeys()))
    return itertools.chain.from_iterable(a if callback(a) else [a] for a in args)

__all__ = _all.diff(globals())
