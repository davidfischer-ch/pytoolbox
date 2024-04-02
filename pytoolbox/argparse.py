"""
Module related to parsing arguments from the command-line.

**Example usage**

>>> from pathlib import Path
>>> from pytoolbox import argparse
>>> parser = argparse.ArgumentParser(epilog='My super cool software.')
>>> x = parser.add_argument('directory', action=argparse.FullPaths, type=argparse.is_dir)
>>> str(parser.parse_args(['/usr/lib']).directory)
'/usr/lib'
>>> assert parser.parse_args(['.']).directory == Path(os.getcwd()).expanduser().resolve()
>>> parser.parse_args(['/does_not_exist/'])
Traceback (most recent call last):
    ...
SystemExit: 2
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Final
import argparse
import getpass
import functools
import os
import sys

from . import console, exceptions, itertools, logging, module
from .decorators import deprecated

log = logging.get_logger(__name__)

_all = module.All(globals())

from argparse import (  # noqa:E402,F401 pylint:disable=unused-import,wrong-import-position
    ArgumentTypeError,
    Namespace
)


# Argument Parsing Actions -------------------------------------------------------------------------


class ChainAction(argparse._AppendAction):  # pylint:disable=protected-access
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: Namespace,
        values,
        option_string: str | None = None
    ) -> None:
        items = getattr(namespace, self.dest, None)
        items = argparse._copy_items(items)  # type: ignore[attr-defined]
        items.extend(itertools.chain(*values))
        setattr(namespace, self.dest, items)


class FullPaths(argparse.Action):
    """
    Expand user/relative paths.

    Credits https://gist.github.com/brantfaircloth/1443543
    """
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: Namespace,
        values,
        option_string: str | None = None
    ) -> None:
        def fullpath(path: Path | str) -> Path:
            return Path(path).expanduser().resolve()
        value = itertools.extract_single([fullpath(v) for v in itertools.chain(values)])
        setattr(namespace, self.dest, value)


# Argument Parsing Types ---------------------------------------------------------------------------


def is_dir(path: Path | str) -> Path:
    """Check if `path` is an actual directory and return it."""
    path = Path(path)
    if path.is_dir():
        return path
    raise argparse.ArgumentTypeError(f'{path} is not a directory')


def is_file(path: Path | str) -> Path:
    """Check if `path` is an actual file and return it."""
    path = Path(path)
    if path.is_file():
        return path
    raise argparse.ArgumentTypeError(f'{path} is not a file')


def multiple(func: Callable[[Any], Any]) -> Callable:
    """Return a list with the result of `func`(value) for value in values."""
    def _multiple(values):
        return [func(v) for v in values] if isinstance(values, list | tuple) else func(values)
    return _multiple


def password(value: str | None) -> str:
    return value or getpass.getpass('Password: ')


def separator(value: str, sep: str | None) -> list[str]:
    """
    Split a string to items using given separator and strip every item, drop empty items.

    Can be used as the type of an argparse argument.
    """
    values = [value.strip()] if sep is None else (v.strip() for v in value.split(sep))
    return [v for v in values if v]


class Range(object):  # pylint:disable=too-few-public-methods

    def __init__(self, type, min, max) -> None:  # pylint:disable=redefined-builtin
        self.type = type
        self.min = min
        self.max = max

    def __call__(self, value):
        try:
            value = self.type(value)
        except Exception as ex:
            raise argparse.ArgumentTypeError(f'Must be of type {self.type.__name__}') from ex
        if not (self.min <= value <= self.max):  # pylint:disable=superfluous-parens
            raise argparse.ArgumentTypeError(f'Must be in range [{self.min}, {self.max}]')
        return value


# Argument Parsing Defaults ------------------------------------------------------------------------


def env_default(name: str) -> dict[str, Any]:
    """Set argument's default value from environment if available else make it mandatory."""
    value = os.getenv(name)
    return {'required': True} if value is None else {'default': value}


# Argument Parsing Configuration Combos ------------------------------------------------------------

DIRECTORY_ARG: Final[dict[str, str | Callable]] = {'action': 'fullpaths', 'type': is_dir}
FILE_ARG: Final[dict[str, str | Callable]] = {'action': 'fullpaths', 'type': is_file}
REMAINDER_ARG: Final[dict[str, Any]] = {'nargs': argparse.REMAINDER}


def MULTI_ARG(sep: str | None = None) -> dict[str, str | Callable]:  # pylint:disable=invalid-name
    return {'action': 'chain', 'nargs': '+', 'type': functools.partial(separator, sep=sep)}


# Argument Parsing Core ----------------------------------------------------------------------------


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


class ArgumentParser(argparse.ArgumentParser):

    formatter_cls: type[argparse.HelpFormatter] = HelpFormatter

    def __init__(self, *args, columns: int | None = None, **kwargs) -> None:
        """Base class to build simple CLIs."""
        console.set_columns(columns)
        kwargs.setdefault('formatter_class', self.formatter_cls)
        super().__init__(*args, **kwargs)
        self.register('action', 'chain', ChainAction)
        self.register('action', 'fullpaths', FullPaths)


class ActionArgumentParser(ArgumentParser):

    def __init__(self, *args, version: str | None = None, **kwargs) -> None:
        """Specialized class to build CLIs that expose actions (sub-commands)."""
        super().__init__(*args, **kwargs)
        self._action = self.add_subparsers(help='action', required=False)
        self._version = version
        if version is not None:
            self.add_version_action(version)

    def action_version(self, args: Namespace) -> None:  # pylint:disable=unused-argument
        print(self._version)

    def add_action(self, name: str, func) -> Callable:
        parser = self._action.add_parser(name, description=func.__doc__)
        parser.set_defaults(func=func)
        return parser.add_argument

    def add_version_action(self, version: str) -> None:
        self._version = version
        self.add_action('version', self.action_version)

    def execute(self, args: Namespace | None = None) -> None:
        args = sys.argv[1:] if args is None else args  # type: ignore[assignment]
        if len(args) < 1:  # type: ignore[arg-type]
            sys.exit('An action is required')
        parsed_args = self.parse_args(args)  # type: ignore[arg-type]
        try:
            parsed_args.func(parsed_args)
        except Exception as ex:  # pylint:disable=broad-exception-caught
            self.handle_exception(ex)
            raise  # If not handled by the exception handler

    def handle_exception(self, ex: Exception) -> None:
        if isinstance(ex, exceptions.CalledProcessError):
            log.error(repr(ex))
            sys.exit(1)
        if isinstance(ex, exceptions.MessageMixin):
            log.error(ex)
            sys.exit(1)


__all__ = _all.diff(globals())


# Deprecated ---------------------------------------------------------------------------------------


@deprecated('Use pytoolbox.console.set_columns instead (drop-in replacement)')
def set_columns(*args, **kwargs) -> int:  # pragma: no cover
    return console.set_columns(*args, **kwargs)


class HelpArgumentParser(ArgumentParser):

    @deprecated('Use pytoolbox.argparse.ArgumentParser instead (drop-in replacement)')
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover
        super().__init__(*args, **kwargs)
