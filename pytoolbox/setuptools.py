"""
Setuptools command extensions.
"""
from __future__ import annotations

import setuptools
import sys


class Disabled(setuptools.Command):  # pylint:disable=duplicate-code
    """A setuptools command that always exits with an error message."""

    description = 'Do not run this.'
    user_options = [('dummy=', 'd', 'dummy option to make setuptools happy')]

    def initialize_options(self) -> None:
        """Initialize options."""

    def finalize_options(self) -> None:
        """Finalize options."""

    def run(self) -> None:
        """Exit immediately with a disabled message."""
        sys.exit('This command is disabled!')
