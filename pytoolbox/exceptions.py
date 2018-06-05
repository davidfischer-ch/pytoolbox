# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import inspect, io, sys, traceback

from . import module
from .encoding import PY2, to_bytes

_all = module.All(globals())


class MessageMixin(Exception):

    message = None

    def __init__(self, message=None, **kwargs):
        if message is not None:
            self.message = message
        self.__dict__.update(kwargs)
        Exception.__init__(self)

    def __unicode__(self):
        attributes = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        return self.message.format(**{a: v for a, v in attributes if a[0] != '_'})

    __str__ = __unicode__


class BadHTTPResponseCodeError(MessageMixin, Exception):
    message = 'Download request {url} code {r_code} expected {code}.'


class CorruptedFileError(MessageMixin, Exception):
    message = 'File {path} is corrupted checksum {file_hash} expected {expected_hash}.'


class ForbiddenError(Exception):
    """A forbidden error."""
    pass


class MultipleSignalHandlersError(MessageMixin, Exception):
    message = """Signal {signum} already handled by {handlers}."""


class TimeoutError(Exception):
    """A time-out error."""
    pass


def assert_raises_item(exception_cls, something, index, value=None, delete=False):
    """

    **Example usage**

    >>> x = {0: 3.14, 1: 2.54}

    Assert that __getitem__ will fail:

    >>> assert_raises_item(KeyError, x, 2)
    >>> assert_raises_item(ValueError, x, 3)
    Traceback (most recent call last):
        ...
    ValueError: Exception KeyError is not an instance of ValueError.
    >>> assert_raises_item(Exception, x, 0)
    Traceback (most recent call last):
        ...
    AssertionError: Exception Exception not raised.

    Assert that __setitem__ will fail:

    >>> assert_raises_item(TypeError, x, [10], value=3.1415)
    >>> assert_raises_item(TypeError, x, 0, value=3.1415)
    Traceback (most recent call last):
        ...
    AssertionError: Exception TypeError not raised.

    Assert that __delitem__ will fail:

    >>> assert_raises_item(KeyError, x, 2, delete=True)
    >>> assert_raises_item(KeyError, x, 1, delete=True)
    Traceback (most recent call last):
        ...
    AssertionError: Exception KeyError not raised.

    >>> x == {0: 3.1415}
    True
    """
    try:
        if delete:
            del something[index]
        elif value is None:
            something[index]
        else:
            something[index] = value
    except Exception as e:
        if not isinstance(e, exception_cls):
            raise ValueError(to_bytes('Exception {0} is not an instance of {1}.'.format(
                             e.__class__.__name__, exception_cls.__name__)))
        return
    raise AssertionError(to_bytes('Exception {0} not raised.'.format(exception_cls.__name__)))


if PY2:
    def get_exception_with_traceback(exception, encoding='utf-8'):
        """
        Return a string with the exception traceback.

        **Example usage**

        If the exception was not raised then there are no traceback:

        >>> from pytoolbox.encoding import to_bytes
        >>> from pytoolbox.unittest import asserts
        >>> asserts.equal(
        ...     get_exception_with_traceback(ValueError(to_bytes('yé'))), 'ValueError: yé\\n')

        If the exception was raised then there is a traceback:

        >>> try:
        ...     raise RuntimeError()
        ... except Exception as e:
        ...     trace = get_exception_with_traceback(e)
        ...     asserts.assert_in('Traceback', trace)
        ...     asserts.assert_in('raise RuntimeError()', trace)
        """
        exception_io = io.BytesIO()
        trace = sys.exc_info()[2] if sys.exc_info()[1] is exception else None
        traceback.print_exception(type(exception), exception, trace, file=exception_io)
        return exception_io.getvalue().decode(encoding)
else:
    def get_exception_with_traceback(exception, encoding='utf-8'):  # pylint:disable=unused-argument
        """
        Return a string with the exception traceback.

        **Example usage**

        If the exception was not raised then there are no traceback:

        >>> from pytoolbox.unittest import asserts
        >>> asserts.equal(get_exception_with_traceback(ValueError('yé')), 'ValueError: yé\\n')

        If the exception was raised then there is a traceback:

        >>> try:
        ...     raise RuntimeError('yé')
        ... except Exception as e:
        ...     trace = get_exception_with_traceback(e)
        ...     asserts.assert_in('Traceback', trace)
        ...     asserts.assert_in("raise RuntimeError('yé')", trace)
        """
        exception_io = io.StringIO()
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=exception_io)
        return exception_io.getvalue()

__all__ = _all.diff(globals())
