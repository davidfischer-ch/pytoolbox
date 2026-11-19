"""
Setuptools command extensions.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, override

import setuptools

# setuptools.Command derives from distutils.core.Command, which exists only through setuptools'
# import hook and stays unknown to a checker; the TYPE_CHECKING branch names the vendored class.
if TYPE_CHECKING:
    from setuptools._distutils.cmd import Command as _Command
else:
    _Command = setuptools.Command


class Disabled(_Command):  # pylint:disable=duplicate-code
    """A setuptools command that always exits with an error message."""

    description = 'Do not run this.'
    user_options = [('dummy=', 'd', 'dummy option to make setuptools happy')]

    @override
    def initialize_options(self) -> None:
        """Initialize options."""

    @override
    def finalize_options(self) -> None:
        """Finalize options."""

    @override
    def run(self) -> None:
        """Exit immediately with a disabled message."""
        sys.exit('This command is disabled!')
