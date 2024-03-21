from __future__ import annotations

from pathlib import Path
from typing import Final
import re

__all__ = [
    'BIT_RATE_REGEX',
    'BIT_RATE_COEFFICIENT_FOR_UNIT',
    'PIPE_REGEX',
    'SIZE_REGEX',
    'SIZE_COEFFICIENT_FOR_UNIT',
    'WIDTH',
    'HEIGHT',
    'is_pipe',
    'to_bit_rate',
    'to_frame_rate',
    'to_size'
]

BIT_RATE_REGEX: Final[re.Pattern] = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-z]+)/s$')
BIT_RATE_COEFFICIENT_FOR_UNIT: Final[dict[str, int]] = {
    'b': 1,
    'k': 1000,
    'm': 1000**2,
    'g': 1000**3
}
PIPE_REGEX: Final[re.Pattern] = re.compile(r'^-$|^pipe:\d+$')
SIZE_REGEX: Final[re.Pattern] = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-zA-Z]+)$')
SIZE_COEFFICIENT_FOR_UNIT: Final[dict[str, int]] = {
    'b': 1,
    'k': 1024,
    'm': 1024**2,
    'g': 1024**3
}

WIDTH: Final[int] = 0
HEIGHT: Final[int] = 1


def is_pipe(path: Path | str) -> bool:
    return isinstance(path, str) and bool(PIPE_REGEX.match(path))


def to_bit_rate(bit_rate: str) -> int | None:
    if match := BIT_RATE_REGEX.match(bit_rate):
        data = match.groupdict()
        return int(float(data['value']) * BIT_RATE_COEFFICIENT_FOR_UNIT[data['units'][0]])
    if bit_rate == 'N/A':
        return None
    raise ValueError(bit_rate)


def to_frame_rate(frame_rate: float | str) -> float | None:
    if isinstance(frame_rate, str) and '/' in frame_rate:
        try:
            num, denom = frame_rate.split('/')
            return float(num) / float(denom)
        except ZeroDivisionError:
            return None
    return float(frame_rate)


def to_size(size: str) -> int:
    if match := SIZE_REGEX.match(size):
        data = match.groupdict()
        return int(float(data['value']) * SIZE_COEFFICIENT_FOR_UNIT[data['units'][0].lower()])
    raise ValueError(size)
