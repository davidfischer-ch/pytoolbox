from pytoolbox import decorators


@decorators.run_once
def increment(counter):
    return counter + 1


@decorators.run_once
def decrement(counter):
    return counter - 1


def test_run_once():
    assert increment(0) == 1
    assert increment(0) is None
    assert decrement(1) == 0
    assert decrement(0) is None
    increment.executed = False
    assert increment(5.5) == 6.5
    assert increment(5.5) is None
