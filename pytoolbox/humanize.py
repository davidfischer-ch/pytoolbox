# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import math, re

from . import module

_all = module.All(globals())

DEFAULT_BITRATE_UNITS = ('bit/s', 'kb/s', 'Mb/s', 'Gb/s', 'Tb/s', 'Pb/s', 'Eb/s', 'Zb/s', 'Yb/s')
DEFAULT_FILESIZE_ARGS = {
    'gnu': {'base': 1000, 'units': ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')},
    'nist': {'base': 1024, 'units': ('B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')},
    'si': {'base': 1000, 'units': ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')},
}
DEFAULT_FREQUENCY_UNITS = ('Hz', 'kHz', 'MHz', 'GHz', 'THz', 'PHz', 'EHz', 'ZHz', 'YHz')
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


def naturalfilesize(bytes, system='nist', format='{sign}{value:.3g} {unit}', scale=None,
                    args=DEFAULT_FILESIZE_ARGS):
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


def naturalfrequency(hz, format='{sign}{value:.3g} {unit}', scale=None,
                     units=DEFAULT_FREQUENCY_UNITS):
    """
    Return a human readable representation of a frequency taking `hz` as the frequency in Hz.

    The unit is taken from:

    * The `scale` if not None (0=bit/s, 1=kb/s, 2=Mb/s, ...).
    * The right scale from `units`.

    **Example usage**

    >>> print(naturalfrequency(-10))
    -10 Hz
    >>> print(naturalfrequency(0.233))
    0.233 Hz
    >>> print(naturalfrequency(69.5, format='{value:.2g} {unit}'))
    70 Hz
    >>> print(naturalfrequency(999.9, format='{value:.0f}{unit}'))
    1000Hz
    >>> print(naturalfrequency(1060))
    1.06 kHz
    >>> print(naturalfrequency(3210837))
    3.21 MHz
    >>> print(naturalfrequency(16262710, units=['Hertz', 'kilo Hertz']))
    1.63e+04 kilo Hertz
    >>> print(naturalfrequency(3210837, scale=1, format='{value:.2f} {unit}'))
    3210.84 kHz
    """
    return _naturalnumber(hz, base=1000, format=format, scale=scale, units=units)


def natural_int_key(text):
    """
    Function to be called as the key argument for list.sort() or sorted() in order to sort
    collections containing textual numbers on a more intuitive way.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> result = sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'])
    >>> asserts.list_equal(result, ['a1', 'a10', 'a19', 'a26', 'a3', 'a4', 'b12', 'b2'])
    >>> result = sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'], key=natural_int_key)
    >>> asserts.list_equal(result, ['a1', 'a3', 'a4', 'a10', 'a19', 'a26', 'b2', 'b12'])
    """
    return [int(c) if c.isdigit() else c for c in DIGIT_REGEX.split(text)]


__all__ = _all.diff(globals())
