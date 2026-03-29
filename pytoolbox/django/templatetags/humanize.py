"""Humanize-related template filters."""

from __future__ import annotations

import datetime as dt

from django.utils.translation import gettext as _

from pytoolbox import humanize
from pytoolbox.datetime import timedelta_to_time
from pytoolbox.private import _parse_kwargs_string

from . import register, string_if_invalid


@register.filter(is_safe=True)
def duration(value: dt.timedelta | None, autoescape: bool = True) -> str:
    """Return a human-readable duration string for the given timedelta value."""
    if value in (None, string_if_invalid):
        return string_if_invalid
    t = timedelta_to_time(value)
    h, m, s = t.hour, t.minute, t.second
    return ' '.join(
        [
            (f'{h} ' + humanize.pluralize(h, _('hour'), _('hours'))) if h else '',
            (f'{m} ' + humanize.pluralize(m, _('minute'), _('minutes'))) if m else '',
            f'{s} ' + humanize.pluralize(s, _('second'), _('seconds')),
        ]
    )


@register.filter(is_safe=True)
def naturalbitrate(bps: float | None, kwargs_string: str | None = None) -> str:
    """
    Return a human readable representation of a bit rate taking `bps` as the rate in bits/s.
    See documentation of :func:`pytoolbox.humanize.naturalbitrate` for further examples.

    Output::

        16487211.33|naturalbitrate -> 16.5 Mb/s
        16487211.33|naturalbitrate:'format={value:.0f} {unit}' -> 16 Mb/s
        16487211.33|naturalbitrate:'format={sign}{value:.0f} {unit}; scale=1' -> 16487 kb/s
        -16487211.33|naturalbitrate:'format={sign}{value:.0f} {unit}' -> -16 Mb/s
        None|naturalbitrate -> (empty string)
        (empty string)|naturalbitrate -> (empty string)
    """
    if bps in (None, string_if_invalid):
        return string_if_invalid
    return humanize.naturalbitrate(
        bps,
        **_parse_kwargs_string(
            kwargs_string,
            format=str,
            scale=int,
        ),
    )


@register.filter(is_safe=True)
def naturalfilesize(the_bytes: float | None, kwargs_string: str | None = None) -> str:
    """
    Return a human readable representation of a *file* size taking `the_bytes` as the size in bytes.
    See documentation of :func:`pytoolbox.humanize.naturalfilesize` for further examples.

    Output::

        16487211.33|naturalfilesize -> 15.7 MB
        16487211.33|naturalfilesize:'system=si' -> 16.5 MiB
        16487211.33|naturalfilesize:'format={value:.0f} {unit}; system=gnu' -> 16 M
        16487211.33|naturalfilesize:'format={sign}{value:.0f} {unit}; scale=1' -> 16101 kB
        -16487211.33|naturalfilesize:'format={sign}{value:.0f} {unit}' -> -16 MB
        None|naturalfilesize -> (empty string)
        (empty string)|naturalfilesize -> (empty string)
    """
    if the_bytes in (None, string_if_invalid):
        return string_if_invalid
    return humanize.naturalfilesize(
        the_bytes,
        **_parse_kwargs_string(
            kwargs_string,
            format=str,
            scale=int,
            system=str,
        ),
    )
