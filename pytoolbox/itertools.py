# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import itertools

from . import module, throttles
from .types import isiterable

_all = module.All(globals())


def chain(*objects, **kwargs):
    """
    Chain the objects, handle non iterable objects gracefully.

    * Set `callback` to a function checking if the object is iterable, defaults to
      :func:`isiterable`.

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
    return itertools.chain.from_iterable(o if callback(o) else [o] for o in objects)


def chunk(objects, length, of_type=list):
    """
    Yield successive chunks of defined `length` from `objects`. Last chunk may be smaller.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> iterable = iter(range(7))
    >>> asserts.list_equal(list(chunk(iterable, 3)), [[0, 1, 2], [3, 4, 5], [6]])
    >>> asserts.list_equal(list(chunk(iterable, 3)), [])
    >>> asserts.list_equal(list(chunk((0, 1, (2, 3)), 1, of_type=set)), [{0}, {1}, {(2, 3)}])
    """
    iterable = iter(objects)
    while True:
        chunk = of_type(itertools.islice(iterable, 0, length))
        if not chunk:
            break
        yield chunk


def extract_single(objects):
    """
    Return the object from objects if there is only one object, else return objects unmodified.

    **Example usage**

    >>> from pytoolbox.unittest import asserts
    >>> asserts.equal(extract_single({6}), 6)
    >>> asserts.list_equal(extract_single([10, 2]), [10, 2])
    >>> asserts.equal(extract_single([7]), 7)
    >>> asserts.equal(extract_single('!'), '!')
    """
    return next(iter(objects)) if len(objects) == 1 else objects


def throttle(objects, min_delay):
    """
    Consume and skips some objects to yield them at defined `min_delay`. First and last objects are
    always returned. This function is a shortcut for
    ``throttles.TimeThrottle(min_delay).throttle_iterable(objects)``.

    **Example usage**

    >>> import datetime, time
    >>> from pytoolbox.unittest import asserts
    >>> def slow_range(*args):
    ...     for i in xrange(*args):
    ...         time.sleep(0.5)
    ...         yield i
    >>> asserts.list_equal(list(throttle(range(10), datetime.timedelta(minutes=1))), [0, 9])
    >>> asserts.list_equal(list(throttle(slow_range(3), '00:00:00.2')), [0, 1, 2])
    """
    return throttles.TimeThrottle(min_delay).throttle_iterable(objects)


__all__ = _all.diff(globals())
