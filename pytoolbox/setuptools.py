"""
Setuptools command extensions.
"""

from __future__ import annotations

import sys

import setuptools

from pytoolbox.compat import override


class Disabled(setuptools.Command):  # pylint:disable=duplicate-code
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
