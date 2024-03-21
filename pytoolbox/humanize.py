from __future__ import annotations

from typing import Final
import math
import re

from . import module

_all = module.All(globals())

DEFAULT_BITRATE_UNITS: Final[tuple[str, ...]] = (
    'bit/s', 'kb/s', 'Mb/s', 'Gb/s', 'Tb/s', 'Pb/s', 'Eb/s', 'Zb/s', 'Yb/s'
)
# pylint:disable=consider-using-namedtuple-or-dataclass)
DEFAULT_FILESIZE_ARGS: Final[dict[str, dict[str, int | tuple[str, ...]]]] = {
    'gnu': {'base': 1000, 'units': ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')},
    'nist': {'base': 1024, 'units': ('B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')},
    'si': {'base': 1000, 'units': ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')}
}
DEFAULT_FREQUENCY_UNITS: Final[tuple[str, ...]] = (
    'Hz', 'kHz', 'MHz', 'GHz', 'THz', 'PHz', 'EHz', 'ZHz', 'YHz'
)
DEFAULT_WEIGHT_UNITS: Final[tuple[str, ...]] = ('g', 'Kg', 'T', 'KT', 'MT', 'GT')
DIGIT_REGEX: Final[re.Pattern] = re.compile(r'(\d+)')

BITRATE_PATTERN: Final[re.Pattern] = re.compile(
    r'(?P<number>[\+-]?\d*\.?\d+([eE]\+\d+)?)\s*(?P<unit>[a-zA-Z]+(/[a-zA-Z]+)?)')

FILESIZE_PATTERN: Final[re.Pattern] = re.compile(
    r'(?P<number>[\+-]?\d*\.?\d+([eE]\+\d+)?)\s*(?P<unit>[a-zA-Z]+)')

FREQUENCY_PATTERN: Final[re.Pattern] = re.compile(
    r'(?P<number>[\+-]?\d*\.?\d+([eE]\+\d+)?)\s*(?P<unit>[a-zA-Z]+)')

WEIGHT_PATTERN: Final[re.Pattern] = re.compile(
    r'(?P<number>[\+-]?\d*\.?\d+([eE]\+\d+)?)\s*(?P<unit>[a-zA-Z]+)')


def naturalbitrate(
    bps: int | float,
    fmt: str = '{sign}{value:.3g} {unit}',
    scale: int | None = None,
    units: tuple[str, ...] = DEFAULT_BITRATE_UNITS
) -> str:
    """
    Return a human readable representation of a bit rate taking `bps` as the rate in bits/s.

    The unit is taken from:

    * The `scale` if not None (0=bit/s, 1=kb/s, 2=Mb/s, ...).
    * The right scale from `units`.

    **Example usage**

    >>> naturalbitrate(-10)
    '-10 bit/s'
    >>> naturalbitrate(0.233)
    '0.233 bit/s'
    >>> naturalbitrate(69.5, fmt='{value:.2g} {unit}')
    '70 bit/s'
    >>> naturalbitrate(999.9, fmt='{value:.0f}{unit}')
    '1000bit/s'
    >>> naturalbitrate(1060)
    '1.06 kb/s'
    >>> naturalbitrate(3210837)
    '3.21 Mb/s'
    >>> naturalbitrate(16262710, units=['bps', 'Kbps'])
    '1.63e+04 Kbps'
    >>> naturalbitrate(3210837, scale=1, fmt='{value:.2f} {unit}')
    '3210.84 kb/s'
    """
    return _natural_number(bps, base=1000, fmt=fmt, scale=scale, units=units)


def naturalfilesize(  # pylint:disable=dangerous-default-value
    size_bytes: int | float,
    system: str = 'nist',
    fmt: str = '{sign}{value:.3g} {unit}',
    scale: int | None = None,
    args: dict[str, dict[str, int | tuple[str, ...]]] = DEFAULT_FILESIZE_ARGS
) -> str:
    """
    Return a human readable representation of a *file* size taking `bytes` as the size in bytes.

    The base and units taken from:

    * The value in `args` with key `system` if not None.
    * The `args` if `system` is None.

    The unit is taken from:

    * The `scale` if not None (0=Bytes, 1=KiB, 2=MiB, ...).
    * The right scale from units previously retrieved from `args`.

    **Example usage**

    >>> naturalfilesize(-10)
    '-10 B'
    >>> naturalfilesize(0.233)
    '0.233 B'
    >>> naturalfilesize(1)
    '1 B'
    >>> naturalfilesize(69.5, fmt='{value:.2g} {unit}')
    '70 B'
    >>> naturalfilesize(999.9, fmt='{value:.0f}{unit}')
    '1000B'
    >>> naturalfilesize(1060)
    '1.04 kB'
    >>> naturalfilesize(1060, system='si')
    '1.06 KiB'
    >>> naturalfilesize(3210837)
    '3.06 MB'
    >>> naturalfilesize(3210837, scale=1, fmt='{value:.2f} {unit}')
    '3135.58 kB'
    >>> naturalfilesize(16262710, system=None, args={'base': 1000, 'units': ['B', 'K']})
    '1.63e+04 K'
    >>> naturalfilesize(314159265358979323846, system='gnu')
    '314 E'
    """
    return _natural_number(  # type: ignore[arg-type]
        size_bytes,
        fmt=fmt,
        scale=scale,
        **(args[system] if system else args))


def naturalfrequency(
    hertz: int | float,
    fmt: str = '{sign}{value:.3g} {unit}',
    scale: int | None = None,
    units: tuple[str, ...] = DEFAULT_FREQUENCY_UNITS
) -> str:  # pylint:disable=dangerous-default-value
    """
    Return a human readable representation of a frequency taking `hertz` as the frequency in Hz.

    The unit is taken from:

    * The `scale` if not None (0=bit/s, 1=kb/s, 2=Mb/s, ...).
    * The right scale from `units`.

    **Example usage**

    >>> naturalfrequency(-10)
    '-10 Hz'
    >>> naturalfrequency(0.233)
    '0.233 Hz'
    >>> naturalfrequency(69.5, fmt='{value:.2g} {unit}')
    '70 Hz'
    >>> naturalfrequency(999.9, fmt='{value:.0f}{unit}')
    '1000Hz'
    >>> naturalfrequency(1060)
    '1.06 kHz'
    >>> naturalfrequency(3210837)
    '3.21 MHz'
    >>> naturalfrequency(16262710, units=['Hertz', 'kilo Hertz'])
    '1.63e+04 kilo Hertz'
    >>> naturalfrequency(3210837, scale=1, fmt='{value:.2f} {unit}')
    '3210.84 kHz'
    """
    return _natural_number(hertz, base=1000, fmt=fmt, scale=scale, units=units)


def naturalweight(
    grams: int | float,
    fmt: str = '{sign}{value:.3g} {unit}',
    scale: int | None = None,
    units: tuple[str, ...] = DEFAULT_WEIGHT_UNITS
) -> str:  # pylint:disable=dangerous-default-value
    """
    Return a human readable representation of a weight in `grams`.

    The unit is taken from:

    * The `scale` if not None (0=g, 1=Kg, 2=T, ...).
    * The right scale from `units`.

    **Example usage**

    >>> naturalweight(-10_000)
    '-10 Kg'
    >>> naturalweight(0.233)
    '0.233 g'
    >>> naturalweight(69.5, fmt='{value:.2g} {unit}')
    '70 g'
    >>> naturalweight(999.9, fmt='{value:.0f}{unit}')
    '1000g'
    >>> naturalweight(545_000)
    '545 Kg'
    >>> naturalweight(3_210_000_000)
    '3.21 KT'
    >>> naturalweight(1_620_000, units=['Grams', 'kilo Grams'])
    '1.62e+03 kilo Grams'
    >>> naturalweight(502456123, scale=2, fmt='{value:.2f} {unit}')
    '502.46 T'
    """
    return _natural_number(grams, base=1000, fmt=fmt, scale=scale, units=units)


def natural_int_key(text: str) -> list[int | str]:
    """
    Function to be called as the key argument for list.sort() or sorted() in order to sort
    collections containing textual numbers on a more intuitive way.

    **Example usage**

    >>> sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'])
    ['a1', 'a10', 'a19', 'a26', 'a3', 'a4', 'b12', 'b2']
    >>> sorted(['a26', 'a1', 'a4', 'a19', 'b2', 'a10', 'a3', 'b12'], key=natural_int_key)
    ['a1', 'a3', 'a4', 'a10', 'a19', 'a26', 'b2', 'b12']
    """
    return [int(c) if c.isdigit() else c for c in DIGIT_REGEX.split(text)]


def parse_bitrate(
    bitrate: str,
    units: tuple[str, ...] = DEFAULT_BITRATE_UNITS,
    pattern: re.Pattern = BITRATE_PATTERN
) -> float:
    """
    Parse a human readable representation of a `bitrate` to its numeric value in bits/s.

    Returned as a natural number you can round if desired.

    **Example usage**

    >>> parse_bitrate('-10 bit/s')
    -10.0
    >>> parse_bitrate('0.233 bit/s')
    0.233
    >>> parse_bitrate('70 bit/s')
    70.0
    >>> parse_bitrate('1000bit/s')
    1000.0
    >>> parse_bitrate('1.06 kb/s')
    1060.0
    >>> parse_bitrate('3.21 Mb/s')
    3210000.0
    >>> parse_bitrate('1.63e+04 Kbps', units=['bps', 'Kbps'])
    16300000.0
    >>> parse_bitrate('3210.84 kb/s')
    3210840.0
    """
    return _parse_natural_number(
        value=bitrate,
        kind='bitrate',
        base=1000,
        units=units,
        pattern=pattern)


def parse_filesize(  # pylint:disable=dangerous-default-value
    size: str,
    system: str = 'nist',
    args: dict[str, dict[str, int | tuple[str, ...]]] = DEFAULT_FILESIZE_ARGS,
    pattern: re.Pattern = FILESIZE_PATTERN
) -> float:
    """
    Parse a human readable representation of a *file* `size` to its numeric value in bytes.

    Returned as a natural number you can round if desired.

    **Example usage**

    >>> parse_filesize('-10 B')
    -10.0
    >>> parse_filesize('0.233 B')
    0.233
    >>> parse_filesize('1 B')
    1.0
    >>> parse_filesize('70 B')
    70.0
    >>> parse_filesize('1000B')
    1000.0
    >>> parse_filesize('1.04 kB')
    1064.96
    >>> parse_filesize('1.06 KiB', system='si')
    1060.0
    >>> parse_filesize('3.06 MB')
    3208642.56
    >>> parse_filesize('3135.58 kB')
    3210833.92
    >>> parse_filesize('1.63e+04 K', system=None, args={'base': 1000, 'units': ['B', 'K']})
    16300000.0
    >>> parse_filesize('314 E', system='gnu')
    3.14e+20
    """
    return _parse_natural_number(  # type: ignore[arg-type]
        value=size,
        kind='file size',
        pattern=pattern,
        **(args[system] if system else args))


def parse_frequency(
    frequency: str,
    units: tuple[str, ...] = DEFAULT_FREQUENCY_UNITS,
    pattern: re.Pattern = FREQUENCY_PATTERN
) -> float:
    """
    Parse a human readable representation of a `frequency` to its numeric value in Hertz.

    Returned as a natural number you can round if desired.

    **Example usage**

    >>> parse_frequency('-10 Hz')
    -10.0
    >>> parse_frequency('0.233 Hz')
    0.233
    >>> parse_frequency(' 70 Hz  ')
    70.0
    >>> parse_frequency('1000Hz')
    1000.0
    >>> parse_frequency('1.06 kHz')
    1060.0
    >>> parse_frequency('3.21 MHz')
    3210000.0
    >>> parse_frequency('3210.84 kHz')
    3210840.0

    >>> parse_frequency('-10 Hertz')
    Traceback (most recent call last):
        ...
    ValueError: No match found '-10 Hertz' 'Hertz' in ('Hz', 'kHz', ...

    >>> parse_frequency('sdlalsdaskla')
    Traceback (most recent call last):
        ...
    ValueError: The value 'sdlalsdaskla' doesn't match frequency pattern.
    """
    return _parse_natural_number(
        value=frequency,
        kind='frequency',
        base=1000,
        units=units,
        pattern=pattern)


def parse_weight(
    weight: str,
    units: tuple[str, ...] = DEFAULT_WEIGHT_UNITS,
    pattern: re.Pattern = WEIGHT_PATTERN
) -> float:
    """
    Parse a human readable representation of a `weight` to its numeric value in grams.

    Returned as a natural number you can round if desired.

    **Example usage**

    >>> parse_weight('-10 Kg')
    -10000.0
    >>> parse_weight('0.233 g')
    0.233
    >>> parse_weight('70 g')
    70.0
    >>> parse_weight(' 1000g  ')
    1000.0
    >>> parse_weight('545 Kg')
    545000.0
    >>> parse_weight('3.21 KT')
    3210000000.0
    >>> parse_weight('502.46 T')
    502460000.0
    """
    return _parse_natural_number(
        value=weight,
        kind='weight',
        base=1000,
        units=units,
        pattern=pattern)


def _natural_number(
    number: int | float,
    base: int,
    units: tuple[str, ...],
    fmt: str = '{sign}{value:.3g} {unit}',
    scale: int | None = None
) -> str:
    sign, number = '' if number >= 0 else '-', abs(number)
    if scale is None:
        scale = min(int(math.log(max(1, number), base)), len(units) - 1)
    unit = units[scale]
    value = number / (base ** scale)
    return fmt.format(sign=sign, value=value, unit=unit)


def _parse_natural_number(
    value: str,
    kind: str,
    base: int,
    units: tuple[str, ...],
    pattern: re.Pattern
) -> float:
    if match := pattern.match(value.strip()):
        data = match.groupdict()
        number = float(data['number'])
        unit = data['unit']
        try:
            index = units.index(unit)
        except ValueError as ex:
            raise ValueError(f'No match found {value!r} {unit!r} in {units}.') from ex
        return number * base ** index
    raise ValueError(f"The value {value!r} doesn't match {kind} pattern.")


__all__ = _all.diff(globals())
