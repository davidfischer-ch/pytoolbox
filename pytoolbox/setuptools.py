from __future__ import annotations

import setuptools
import sys


class Disabled(setuptools.Command):  # pylint:disable=duplicate-code

    description = 'Do not run this.'
    user_options = [('dummy=', 'd', 'dummy option to make setuptools happy')]

    def initialize_options(self):
        """Initialize options."""

    def finalize_options(self):
        """Finalize options."""

    def run(self):
        sys.exit('This command is disabled!')
