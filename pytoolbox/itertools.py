from __future__ import annotations

import itertools

from . import throttles
from .types import isiterable

__all__ = ['chain', 'chunk', 'extract_single', 'throttle']


def chain(*objects, callback=isiterable):
    """
    Chain the objects, handle non iterable objects gracefully.

    * Set `callback` to a function checking if the object is iterable, defaults to
      :func:`isiterable`.

    **Example usage**

    >>> list(chain(1, 2, '3', [4, 5], {6: 7}))
    [1, 2, '3', 4, 5, 6]
    >>> list(chain(1, 2, '3', callback=lambda a: True))
    Traceback (most recent call last):
        ...
    TypeError: 'int' object is not iterable
    """
    return itertools.chain.from_iterable(o if callback(o) else [o] for o in objects)


def chunk(objects, length, of_type=list):
    """
    Yield successive chunks of defined `length` from `objects`. Last chunk may be smaller.

    Python 3.12 introduced :func:`itertools.batched` (but without `of_type` conversion).

    **Example usage**

    >>> iterable = iter(list(range(7)))
    >>> list(chunk(iterable, 3))
    [[0, 1, 2], [3, 4, 5], [6]]
    >>> list(chunk(iterable, 3))
    []
    >>> list(chunk((0, 1, (2, 3)), 1, of_type=set))
    [{0}, {1}, {(2, 3)}]
    """
    iterable = iter(objects)
    while (data := of_type(itertools.islice(iterable, 0, length))):
        yield data


def extract_single(objects):
    """
    Return the object from objects if there is only one object, else return objects unmodified.

    **Example usage**

    >>> extract_single({6})
    6
    >>> extract_single([10, 2])
    [10, 2]
    >>> extract_single([7])
    7
    >>> extract_single('!')
    '!'
    """
    return next(iter(objects)) if len(objects) == 1 else objects


def throttle(objects, min_delay):
    """
    Consume and skips some objects to yield them at defined `min_delay`. First and last objects are
    always returned. This function is a shortcut for
    ``throttles.TimeThrottle(min_delay).throttle_iterable(objects)``.

    **Example usage**

    >>> import datetime
    >>> import time
    >>>
    >>> def slow_range(*args):
    ...     for i in range(*args):
    ...         time.sleep(0.5)
    ...         yield i
    ...
    >>> list(throttle(list(range(10)), datetime.timedelta(minutes=1)))
    [0, 9]
    >>> list(throttle(slow_range(3), '00:00:00.2'))
    [0, 1, 2]
    """
    return throttles.TimeThrottle(min_delay).throttle_iterable(objects)
