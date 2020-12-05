import inspect, io, traceback

from . import module

_all = module.All(globals())


class MessageMixin(Exception):

    message = None

    def __init__(self, message=None, **kwargs):
        if message is not None:
            self.message = message
        self.__dict__.update(kwargs)
        Exception.__init__(self)

    def __str__(self):
        attributes = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        return self.message.format(**{a: v for a, v in attributes if a[0] != '_'})


class BadHTTPResponseCodeError(MessageMixin, Exception):
    message = 'Download request {url} code {r_code} expected {code}.'


class CorruptedFileError(MessageMixin, Exception):
    message = 'File {path} is corrupted checksum {file_hash} expected {expected_hash}.'


class ForbiddenError(Exception):
    """A forbidden error."""


class InvalidBrandError(MessageMixin, Exception):
    message = 'Brand {brand} not in {brands}.'


class InvalidIPSocketError(MessageMixin, Exception):
    message = '{socket} is not a valid IP socket.'


class MultipleSignalHandlersError(MessageMixin, Exception):
    message = 'Signal {signum} already handled by {handlers}.'


class UndefinedPathError(Exception):
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
            something[index]  # pylint:disable=pointless-statement
        else:
            something[index] = value
    except Exception as e:  # pylint:disable=broad-except
        if not isinstance(e, exception_cls):
            raise ValueError(
                f'Exception {e.__class__.__name__} is not '
                f'an instance of {exception_cls.__name__}.') from e
        return
    raise AssertionError(f'Exception {exception_cls.__name__} not raised.')


def get_exception_with_traceback(exception):
    """
    Return a string with the exception traceback.

    **Example usage**

    If the exception was not raised then there are no traceback:

    >>> get_exception_with_traceback(ValueError('yé'))
    'ValueError: yé\\n'

    If the exception was raised then there is a traceback:

    >>> try:
    ...     raise RuntimeError('yé')
    ... except Exception as e:
    ...     trace = get_exception_with_traceback(e)
    >>> 'Traceback' in trace
    True
    >>> "raise RuntimeError('yé')" in trace
    True
    """
    buf = io.StringIO()
    traceback.print_exception(type(exception), exception, exception.__traceback__, file=buf)
    return buf.getvalue()


__all__ = _all.diff(globals())
