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

import numbers, re

from ... import module
from ...encoding import string_types

_all = module.All(globals())

BIT_RATE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-z]+)/s$')
BIT_RATE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1000, 'm': 1000**2, 'g': 1000**3}
PIPE_REGEX = re.compile(r'^-$|^pipe:\d+$')
SIZE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-zA-Z]+)$')
SIZE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1024, 'm': 1024**2, 'g': 1024**3}
WIDTH, HEIGHT = range(2)


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
