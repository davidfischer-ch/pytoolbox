from __future__ import annotations

from pytoolbox import decorators


@decorators.run_once
def increment(counter: int) -> int:
    return counter + 1


@decorators.run_once
def decrement(counter: int) -> int:
    return counter - 1


def test_run_once() -> None:
    assert increment(0) == 1
    assert increment(0) is None
    assert decrement(1) == 0
    assert decrement(0) is None
    increment.executed = False  # type: ignore[attr-defined]
    assert increment(5.5) == 6.5
    assert increment(5.5) is None
