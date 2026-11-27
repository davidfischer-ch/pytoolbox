"""Tests for the collections module."""

from __future__ import annotations

from pytoolbox.collections import EventsTable, pygal_deque


def test_events_table_get_maps_time_to_correct_event() -> None:
    """A time maps to the event of its slot, each slot lasting 3600 / speedup seconds."""
    table = EventsTable({0: 'midnight', 1: 'dawn', 12: 'noon'}, time_range=24, time_speedup=24)
    assert table.get(0) == (0, 'midnight')
    assert table.get(150) == (1, 'dawn')
    assert table.get(1800) == (12, 'noon')


def test_events_table_sparse_fills_gaps_with_previous() -> None:
    """Sparse table fills missing indices with the last defined event."""
    table = EventsTable({0: 'only'}, time_range=4, time_speedup=1)
    for i in range(4):
        assert table.events[i] == 'only'


def test_pygal_deque() -> None:
    """Deque tracks last non-None value per slot; fill mode replaces Nones with last value."""
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


def test_pygal_deque_list_empty_with_last_set() -> None:
    """An empty deque lists as empty, even with a last value set."""
    data = pygal_deque()
    data.last = 42
    assert not data.list()
