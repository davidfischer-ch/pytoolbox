# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import math

__all__ = ('DEFAULT_UNITS', 'naturalbitrate')

DEFAULT_UNITS = ('bit/s', 'kb/s', 'Mb/s', 'Gb/s', 'Tb/s', 'Pb/s', 'Eb/s', 'Zb/s', 'Yb/s')


def naturalbitrate(bps, format='{sign}{value:.3g} {unit}', scale=None, units=DEFAULT_UNITS):
    """
    Return the bitrate ``bps`` (integer value in bit/s) converted to a string with unit taken from:

    * The ``scale`` if not None (0=bit/s, 1=kb/s, 2=Mb/s, ...).
    * The right scale from ``units``.

    **Example usage**

    >>> print(naturalbitrate(-10))
    -10 bit/s
    >>> print(naturalbitrate(0))
    0 bit/s
    >>> print(naturalbitrate(69.5, format='{value:.2g} {unit}'))
    70 bit/s
    >>> print(naturalbitrate(999.9, format='{value:.0f}{unit}'))
    1000bit/s
    >>> print(naturalbitrate(1060))
    1.06 kb/s
    >>> print(naturalbitrate(3210837))
    3.21 Mb/s
    >>> print(naturalbitrate(3210837, scale=1, format='{value:.2f} {unit}'))
    3210.84 kb/s
    """
    sign, bps = '' if bps >= 0 else '-', abs(bps)
    scale = int(math.log10(bps or 1) // 3 if scale is None else scale)
    unit = units[scale]
    value = bps / (1000 ** scale)
    return format.format(sign=sign, value=value, unit=unit)
