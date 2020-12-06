import setuptools, sys


class Disabled(setuptools.Command):  # pylint:disable=duplicate-code

    description = 'Do not run this.'
    user_options = [('dummy=', 'd', 'dummy option to make setuptools happy')]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):  # pylint:disable=no-self-use
        sys.exit('This command is disabled!')
