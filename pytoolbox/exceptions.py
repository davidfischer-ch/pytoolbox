from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any
import inspect
import io
import traceback

from . import module

_all = module.All(globals())

# TODO Use pydantic or dataclass or StrongTypedMixin kind of?


class MessageMixin(Exception):
    attrs: Annotated[tuple[str, ...], 'Attributes to expose to the __repr__'] = tuple()
    message: str

    def __init__(self, message: str | None = None, **kwargs) -> None:
        assert hasattr(self, 'message'), type(self)          # TODO metaclass to check this
        assert set(self.attrs).issubset(set(kwargs.keys()))  # TODO metaclass to check this
        if message is not None:
            self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)
        super().__init__()

    def __repr__(self) -> str:
        args = [] if self.message == type(self).message else [f'{repr(self.message)}']
        args.extend(f'{a}={repr(getattr(self, a))}' for a in self.attrs)
        return f"{self.__class__.__name__}({', '.join(args)})"

    def __str__(self) -> str:
        attributes = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        return self.message.format(**{a: v for a, v in attributes if a[0] != '_'})


class BadHTTPResponseCodeError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('url', 'r_code', 'code')
    message: str = 'Download request {url} code {r_code} expected {code}.'
    url: str
    r_code: int
    code: int


class CalledProcessError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('returncode', 'cmd', 'stdout', 'stderr')
    message: str = 'Process {cmd!r} failed with return code {returncode}'
    returncode: int
    cmd: str
    stdout: bytes | None
    stderr: bytes | None


class CorruptedFileError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('path', 'file_hash', 'expected_hash')
    message: str = 'File {path} is corrupted checksum {file_hash} expected {expected_hash}.'
    path: Path
    file_hash: str
    expected_hash: str


class DuplicateGitTagError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('tag', )
    message: str = 'Tag {tag} already exist.'
    tag: str


class ForbiddenError(Exception):
    """A forbidden error."""


class GitReferenceError(MessageMixin, Exception):
    attrs: tuple[str, ...] = tuple()
    message: str = 'Unable to detect current Git reference.'


class InvalidBrandError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('brand', 'brands')
    message: str = 'Brand {brand} not in {brands}.'
    brand: str
    brands: set[str]


class InvalidIPSocketError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('socket', )
    message: str = '{socket} is not a valid IP socket.'
    socket: str


class MultipleSignalHandlersError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('signum', 'handlers', )
    message: str = 'Signal {signum} already handled by {handlers}.'
    signum: str
    handlers: list[Callable]


class RegexMatchGroupNotFoundError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('group', )
    message: str = 'Group "{group}" not found in the regex match.'
    group: str


class SSHAgentConnectionError(MessageMixin, Exception):
    message: str = 'Unable to communicate with the ssh agent.'


class SSHAgentLoadingKeyError(MessageMixin, Exception):
    message: str = 'Unable to load key.'


class SSHAgentParsingError(MessageMixin, Exception):
    attrs: tuple[str, ...] = ('output', )
    message: str = 'Unable to parse ssh-agent output "{output}".'
    output: str


class UndefinedPathError(Exception):
    pass


def assert_raises_item(
    exception_cls: type[Exception],
    something: Any,  # That has __getitem__
    index: Any,
    value: Any | None = None,
    delete: bool = False
) -> None:
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
    except Exception as ex:  # pylint:disable=broad-except
        if not isinstance(ex, exception_cls):
            raise ValueError(
                f'Exception {ex.__class__.__name__} is not '
                f'an instance of {exception_cls.__name__}.') from ex
        return
    raise AssertionError(f'Exception {exception_cls.__name__} not raised.')


def get_exception_with_traceback(exception: Exception) -> str:
    """
    Return a string with the exception traceback.

    **Example usage**

    If the exception was not raised then there are no traceback:

    >>> get_exception_with_traceback(ValueError('yé'))
    'ValueError: yé\\n'

    If the exception was raised then there is a traceback:

    >>> try:
    ...     raise RuntimeError('yé')
    ... except Exception as ex:
    ...     trace = get_exception_with_traceback(ex)
    >>> 'Traceback' in trace
    True
    >>> "raise RuntimeError('yé')" in trace
    True
    """
    buf = io.StringIO()
    traceback.print_exception(type(exception), exception, exception.__traceback__, file=buf)
    return buf.getvalue()


__all__ = _all.diff(globals())
