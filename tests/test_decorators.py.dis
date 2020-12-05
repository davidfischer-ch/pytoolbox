from pytoolbox import decorators

from . import base


class TestDecorators(base.TestCase):

    tags = ('decorators', )

    def test_run_once(self):

        @decorators.run_once
        def increment(counter):
            return counter + 1

        @decorators.run_once
        def decrement(counter):
            return counter - 1

        self.equal(increment(0), 1)
        self.is_none(increment(0))
        self.equal(decrement(1), 0)
        self.is_none(decrement(0))
        increment.executed = False
        self.equal(increment(5.5), 6.5)
        self.is_none(increment(5.5))
