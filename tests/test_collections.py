"""Tests for the collections module."""

from __future__ import annotations

import copy
import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, override

import pytest

from pytoolbox.collections import EventsTable, merge_dicts, pygal_deque

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def test_merge_dicts_deep_copies_each_value_once() -> None:
    """Each input value is copied once per call, whatever the number of inputs and the depth."""
    copied: list[Any] = []

    class Leaf:  # pylint:disable=too-few-public-methods
        """A value recording each of its copies."""

        def __deepcopy__(self, memo: dict[int, Any]) -> Self:
            copied.append(self)
            return type(self)()

    leaves = [Leaf() for _ in range(4)]
    inputs = [{'k': {'k': {'k': {index: leaf}}}} for index, leaf in enumerate(leaves)]

    merged = merge_dicts(*inputs, deep=True)

    assert copied == leaves
    assert list(merged['k']['k']['k']) == [0, 1, 2, 3]


def test_merge_dicts_deep_keeps_a_cycle() -> None:
    """A mapping holding itself, merged with itself, gives a copy holding itself."""
    cyclic: dict[str, dict[str, Any]] = {'x': {}}
    cyclic['x']['self'] = cyclic['x']

    merged = merge_dicts(cyclic, cyclic, deep=True)

    assert merged['x'] is not cyclic['x']
    assert merged['x']['self'] is merged['x']


def test_merge_dicts_deep_keeps_shared_mappings_shared() -> None:
    """A mapping held in several places of one dictionary is copied once and stays shared."""
    shared = {'a': 1}

    merged = merge_dicts({'p': shared, 'q': shared}, deep=True)

    assert merged['p'] is merged['q']
    assert merged['p'] is not shared


def test_merge_dicts_deep_merges_deeper_than_the_recursion_limit() -> None:
    """A merge deeper than the recursion limit completes, and merges every level."""
    depth = 2 * sys.getrecursionlimit()
    loop: dict[str, Any] = {'loop': True}
    loop['next'] = loop
    chain: dict[str, Any] = {}
    for level in reversed(range(depth)):
        chain = {'level': level, 'next': chain}

    node = merge_dicts(loop, chain, deep=True)

    for level in range(depth):
        assert (node['level'], node['loop']) == (level, True)
        node = node['next']
    assert 'level' not in node
    assert node['next']['next'] is node['next']


def test_merge_dicts_deep_merges_identity_keys_at_every_depth() -> None:
    """A key hashed by identity matches itself at every depth, and the result holds its copy."""

    class Key:  # pylint:disable=too-few-public-methods
        """A key equal to itself only."""

    key = Key()

    top = merge_dicts({key: {'x': 1}}, {key: {'y': 2}}, deep=True)
    nested = merge_dicts({'a': {key: {'x': 1}}}, {'a': {key: {'y': 2}}}, deep=True)['a']

    for merged in (nested, top):
        assert list(merged.values()) == [{'x': 1, 'y': 2}]
        assert key not in merged


def test_merge_dicts_deep_merges_mappings_at_every_depth() -> None:
    """A mapping in both dictionaries merges key by key, down to the deepest level."""
    assert merge_dicts(
        {'a': {'b': {'c': 1, 'd': 1}, 'e': 1}, 'f': 1},
        {'a': {'b': {'d': 2, 'g': 2}}},
        {'a': {'b': {'g': 3}, 'h': 3}},
        deep=True,
    ) == {'a': {'b': {'c': 1, 'd': 2, 'g': 3}, 'e': 1, 'h': 3}, 'f': 1}


@pytest.mark.parametrize('depth', [3, 40])
def test_merge_dicts_deep_merges_shared_mappings_once(depth: int) -> None:
    """A pair of shared mappings is merged once and stays shared, keeping the work linear."""
    dag: dict[str, Any] = {'leaf': 1}
    for _ in range(depth):
        dag = {'x': dag, 'y': dag}

    node = merge_dicts({'v': dag}, {'v': dag}, deep=True)['v']

    assert node is not dag
    for _ in range(depth):
        assert node['x'] is node['y']
        node = node['x']
    assert node == {'leaf': 1}


def test_merge_dicts_deep_merges_two_cycles_of_coprime_lengths() -> None:
    """Two cycles merge into one whose length is the least common multiple of theirs."""

    def ring(side: str, length: int) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = [{side: index} for index in range(length)]
        for index, node in enumerate(nodes):
            node['next'] = nodes[(index + 1) % length]
        return nodes[0]

    start = node = merge_dicts({'v': ring('left', 40)}, {'v': ring('right', 41)}, deep=True)['v']

    for step in range(40 * 41):
        assert (node['left'], node['right']) == (step % 40, step % 41)
        node = node['next']
    assert node is start


def test_merge_dicts_deep_merges_values_built_on_access() -> None:
    """A mapping building a new value on each access merges each one under its own key."""
    keys = [f'k{index}' for index in range(6)]

    class BuiltOnAccess(Mapping[str, dict[str, str]]):
        """A mapping whose values live only as long as the caller holds them."""

        @override
        def __getitem__(self, key: str) -> dict[str, str]:
            return {'from': key}

        @override
        def __iter__(self) -> Iterator[str]:
            return iter(keys)

        @override
        def __len__(self) -> int:
            return len(keys)

    shared = {'base': 1}

    merged = merge_dicts(dict.fromkeys(keys, shared), BuiltOnAccess(), deep=True)

    assert merged == {key: {'base': 1, 'from': key} for key in keys}


def test_merge_dicts_deep_replaces_a_list_or_a_scalar() -> None:
    """A list replaces the previous value, as a scalar does, and a scalar replaces a mapping."""
    assert merge_dicts(
        {'a': [1, 2], 'b': {'c': 1}},
        {'a': [3], 'b': 2},
        deep=True,
    ) == {'a': [3], 'b': 2}


def test_merge_dicts_deep_shares_no_nested_value() -> None:
    """The result holds copies: changing it leaves the inputs as they were."""
    first: dict[str, Any] = {'a': {'b': [1]}, 'c': {'d': 1}}
    second: dict[str, Any] = {'a': {'e': [2]}, 'f': [3]}

    merged = merge_dicts(first, second, deep=True)

    assert merged['a'] is not first['a']
    assert merged['a']['b'] is not first['a']['b']
    assert merged['a']['e'] is not second['a']['e']
    assert merged['c'] is not first['c']
    assert merged['f'] is not second['f']


@pytest.mark.parametrize('deep', [False, True])
def test_merge_dicts_does_not_mutate_the_inputs(deep: bool) -> None:
    """The inputs keep their content in either mode."""
    first = {'a': {'b': {'c': 1}}, 'd': [1]}
    second = {'a': {'b': {'c': 2, 'e': 2}}, 'd': [2]}
    original_first = copy.deepcopy(first)
    original_second = copy.deepcopy(second)

    merge_dicts(first, second, deep=deep)

    assert first == original_first
    assert second == original_second


def test_merge_dicts_shallow_by_default() -> None:
    """Without `deep`, a mapping replaces the previous one, and the result shares the values."""
    first = {'a': {'b': 1}}
    second = {'a': {'c': 2}, 'd': [1]}

    merged = merge_dicts(first, second)

    assert merged == {'a': {'c': 2}, 'd': [1]}
    assert merged['a'] is second['a']
    assert merged['d'] is second['d']


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
