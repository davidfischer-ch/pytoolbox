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

import math, re

__all__ = ('DEFAULT_BITRATE_UNITS', 'DEFAULT_FILESIZE_ARGS', 'naturalbitrate', 'naturalfilesize', 'natural_int_key')

DEFAULT_BITRATE_UNITS = ('bit/s', 'kb/s', 'Mb/s', 'Gb/s', 'Tb/s', 'Pb/s', 'Eb/s', 'Zb/s', 'Yb/s')
DEFAULT_FILESIZE_ARGS = {
    'gnu': {'base': 1000, 'units': ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')},
    'nist': {'base': 1024, 'units': ('B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')},
    'si': {'base': 1000, 'units': ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')},
}
DIGIT_REGEX = re.compile(r'(\d+)')


def _naturalnumber(number, base, units, format='{sign}{value:.3g} {unit}', scale=None):
    sign, number = '' if number >= 0 else '-', abs(number)
    if scale is None:
        scale = min(int(math.log(max(1, number), base)), len(units) - 1)
    unit = units[scale]
    value = number / (base ** scale)
    return format.format(sign=sign, value=value, unit=unit)


def naturalbitrate(bps, format='{sign}{value:.3g} {unit}', scale=None, units=DEFAULT_BITRATE_UNITS):
    """
    Return a human readable representation of a bit rate taking `bps` as the rate in bits/s.

    The unit is taken from:

    * The `scale` if not None (0=bit/s, 1=kb/s, 2=Mb/s, ...).
    * The right scale from `units`.

    **Example usage**

    >>> print(naturalbitrate(-10))
    -10 bit/s
    >>> print(naturalbitrate(0.233))
    0.233 bit/s
    >>> print(naturalbitrate(69.5, format='{value:.2g} {unit}'))
    70 bit/s
    >>> print(naturalbitrate(999.9, format='{value:.0f}{unit}'))
    1000bit/s
    >>> print(naturalbitrate(1060))
    1.06 kb/s
    >>> print(naturalbitrate(3210837))
    3.21 Mb/s
    >>> print(naturalbitrate(16262710, units=['bps', 'Kbps']))
    1.63e+04 Kbps
    >>> print(naturalbitrate(3210837, scale=1, format='{value:.2f} {unit}'))
    3210.84 kb/s
    """
    return _naturalnumber(bps, base=1000, format=format, scale=scale, units=units)


def naturalfilesize(bytes, system='nist', format='{sign}{value:.3g} {unit}', scale=None, args=DEFAULT_FILESIZE_ARGS):
    """
    Return a human readable representation of a *file* size taking `bytes` as the size in bytes.

    The base and units taken from:

    * The value in `args` with key `system` if not None.
    * The `args` if `system` is None.

    The unit is taken from:

    * The `scale` if not None (0=Bytes, 1=KiB, 2=MiB, ...).
    * The right scale from units previously retrieved from `args`.

    **Example usage**

    >>> print(naturalfilesize(-10))
    -10 B
    >>> print(naturalfilesize(0.233))
    0.233 B
    >>> print(naturalfilesize(1))
    1 B
    >>> print(naturalfilesize(69.5, format='{value:.2g} {unit}'))
    70 B
    >>> print(naturalfilesize(999.9, format='{value:.0f}{unit}'))
    1000B
    >>> print(naturalfilesize(1060))
    1.04 kB
    >>> print(naturalfilesize(1060, system='si'))
    1.06 KiB
    >>> print(naturalfilesize(3210837))
    3.06 MB
    >>> print(naturalfilesize(3210837, scale=1, format='{value:.2f} {unit}'))
    3135.58 kB
    >>> print(naturalfilesize(16262710, system=None, args={'base': 1000, 'units': ['B', 'K']}))
    1.63e+04 K
    >>> print(naturalfilesize(314159265358979323846, system='gnu'))
    314 E
    """
    return _naturalnumber(bytes, format=format, scale=scale, **(args[system] if system else args))


def natural_int_key(text):
    """
    Function to be called as the key argument for list.sort() or sorted() in order to sort collections containing
    textual numbers on a more intuitive way.

    **Example usage**

    >>> from nose.tools import eq_
    >>> result = sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'])
    >>> eq_(result, ['a1', 'a10', 'a19', 'a26', 'a3', 'a4', 'b12', 'b2'])
    >>> result = sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'], key=natural_int_key)
    >>> eq_(result, ['a1', 'a3', 'a4', 'a10', 'a19', 'a26', 'b2', 'b12'])
    """
    return [int(c) if c.isdigit() else c for c in DIGIT_REGEX.split(text)]
