# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import numbers, re

from pytoolbox import module
from pytoolbox.encoding import string_types

_all = module.All(globals())

BIT_RATE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-z]+)/s$')
BIT_RATE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1000, 'm': 1000**2, 'g': 1000**3}
PIPE_REGEX = re.compile(r'^-$|^pipe:\d+$')
SIZE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-zA-Z]+)$')
SIZE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1024, 'm': 1024**2, 'g': 1024**3}
WIDTH, HEIGHT = xrange(2)  # noqa


def is_pipe(path):
    return isinstance(path, string_types) and PIPE_REGEX.match(path)


def to_bit_rate(bit_rate):
    match = BIT_RATE_REGEX.match(bit_rate)
    if match:
        match = match.groupdict()
        return int(float(match['value']) * BIT_RATE_COEFFICIENT_FOR_UNIT[match['units'][0]])
    if bit_rate == 'N/A':
        return None
    raise ValueError(bit_rate)


def to_frame_rate(frame_rate):
    if isinstance(frame_rate, numbers.Number):
        return frame_rate
    if '/' in frame_rate:
        try:
            num, denom = frame_rate.split('/')
            return float(num) / float(denom)
        except ZeroDivisionError:
            return None
    return float(frame_rate)


def to_size(size):
    match = SIZE_REGEX.match(size)
    if match:
        match = match.groupdict()
        return int(float(match['value']) * SIZE_COEFFICIENT_FOR_UNIT[match['units'][0].lower()])
    raise ValueError(size)


__all__ = _all.diff(globals())
