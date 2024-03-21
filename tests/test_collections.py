from __future__ import annotations

from pytoolbox.collections import pygal_deque


def test_pygal_deque() -> None:
    data = pygal_deque(maxlen=4)
    data.append(5)
    assert data.list(fill=False) == [5]
    data.append(5)
    data.append(5)
    assert data.list(fill=False) == [5, None, 5]
    data.append(5)
    assert data.list(fill=False) == [5, None, None, 5]
    data.append(5)
    assert data.list(fill=False) == [5, None, None, 5]
    data.append(None)
    assert data.list(fill=False) == [5, None, None, 5]
    data.append(None)
    assert data.list(fill=False) == [5, None, None, 5]
    data.append(5)
    assert data.list(fill=False) == [5, None, None, 5]
    assert data.list(fill=True) == [5, 5, 5, 5]
    data.append(1)
    assert data.list(fill=False) == [5, None, 5, 1]
    data.append(None)
    assert data.list(fill=False) == [5, 5, 1, 1]
    data.append(None)
    assert data.list(fill=False) == [5, 1, None, 1]
    assert data.list(fill=True) == [5, 1, 1, 1]
    data.append(None)
    assert data.list(fill=False) == [1, None, None, 1]
    data.append(2)
    data.append(3)
    assert data.list(fill=False) == [1, 1, 2, 3]
    data.append(None)
    data.append(2)
    assert data.list(fill=False) == [2, 3, 3, 2]
