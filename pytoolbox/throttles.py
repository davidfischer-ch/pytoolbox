"""
Throttling classes implementing various throttling policies.
"""
from __future__ import annotations

import time

from .datetime import total_seconds
from .types import Missing

__all__ = ['TimeThrottle', 'TimeAndRatioThrottle']


class TimeThrottle(object):
    """
    Time based throttling class.

    >>> import datetime
    >>> def slow_range(*args):
    ...     for i in range(*args):
    ...         time.sleep(0.5)
    ...         yield i
    >>> t1, t2 = (TimeThrottle(t) for t in (datetime.timedelta(minutes=1), 0.2))
    >>> list(t1.throttle_iterable((i, i) for i in range(10)))
    [(0, 0), (9, 9)]
    >>> list(t2.throttle_iterable(slow_range(3)))
    [0, 1, 2]
    """

    def __init__(self, min_time_delta) -> None:
        self.min_time_delta: float = total_seconds(min_time_delta)
        self.previous_time = None

    def is_throttled(self) -> bool:
        """Return a boolean indicating if you should throttle."""
        if not self.previous_time:
            self._update()
            return False
        if time.time() - self.previous_time >= total_seconds(self.min_time_delta):
            self._update()
            return False
        return True

    def throttle_iterable(self, objects, callback=lambda o: None):
        """
        Consume and skips some objects to yield them at defined `min_delay`. First and last objects
        are always returned.

        * Set `callback` to a callable with the signature ``is_throttled_args = callback(object)``.
          Used by subclasses.
        """
        current_object = Missing
        for obj in objects:
            current_object = obj
            args = callback(obj) or ()
            if not self.is_throttled(*args):
                current_object = Missing
                yield obj
        if current_object is not Missing:
            yield current_object

    def _update(self):
        self.previous_time = time.time()


class TimeAndRatioThrottle(TimeThrottle):
    """
    Time and ratio based throttling class.

    >>> import datetime
    >>> def slow_range(*args):
    ...     for i in range(*args):
    ...         time.sleep(0.5)
    ...         yield i
    >>> t1, t2 = (TimeAndRatioThrottle(0.3, t, 10*t) for t in (datetime.timedelta(minutes=1), 0.4))
    >>> list(t1.throttle_iterable(list(range(9)), lambda i: [i/9]))
    [0, 8]
    >>> list(t2.throttle_iterable(slow_range(9), lambda i: [i/9]))
    [0, 3, 6, 8]
    """

    def __init__(self, min_ratio_delta, min_time_delta, max_time_delta):
        super().__init__(min_time_delta)
        self.min_ratio_delta = total_seconds(min_ratio_delta)
        self.max_time_delta = total_seconds(max_time_delta)
        self.previous_ratio = 0

    def is_throttled(self, ratio):  # pylint:disable=arguments-differ
        """Return a boolean indicating if you should throttle."""
        if not self.previous_time:
            self._update(ratio)
            return False
        ratio_delta = ratio - self.previous_ratio
        time_delta = time.time() - self.previous_time
        if (
            ratio_delta > self.min_ratio_delta
            and time_delta > self.min_time_delta
            or time_delta > self.max_time_delta
        ):
            self._update(ratio)
            return False
        return True

    def _update(self, ratio):  # pylint:disable=arguments-differ
        super()._update()
        self.previous_ratio = ratio
