"""
State machine enumerations with transition validation.
"""

from __future__ import annotations

import collections
import inspect
from collections.abc import Collection, Mapping
from typing import Any, ClassVar

__all__ = ['StateEnumMetaclass', 'StateEnumMergeMetaclass', 'StateEnum']


class StateEnumMetaclass(type):
    """Metaclass that computes state sets and inverse transitions from ``TRANSITIONS``."""

    # TODO type hint class attributes?

    def __init__(cls, name: str, bases: tuple[type, ...], cls_dict: dict[str, Any]) -> None:
        super().__init__(name, bases, cls_dict)
        if hasattr(cls, 'TRANSITIONS'):
            cls.ALL_STATES = frozenset(cls.TRANSITIONS.keys())
            cls.FINAL_STATES = frozenset(s for s, t in cls.TRANSITIONS.items() if not t)
            # Every state has its entry, empty for a state no transition leads into.
            inverse_transitions = collections.defaultdict(set, {s: set() for s in cls.TRANSITIONS})
            for state, transitions in cls.TRANSITIONS.items():
                for transition in transitions:
                    inverse_transitions[transition].add(state)
            cls.INVERSE_TRANSITIONS = {s: frozenset(t) for s, t in inverse_transitions.items()}


class StateEnumMergeMetaclass(StateEnumMetaclass):
    """Metaclass that merges transitions from multiple base state enums."""

    # TODO type hint class attributes?

    def __init__(cls, name: str, bases: tuple[type, ...], cls_dict: dict[str, Any]) -> None:
        # Retrieve base "state" classes attributes
        m_states, transitions = collections.defaultdict(set), collections.defaultdict(set)
        for base in bases:
            for key, value in (i for i in inspect.getmembers(base) if i[0].endswith('_STATES')):
                m_states[key].update(value)
            for key, values in base.TRANSITIONS.items():  # type: ignore[attr-defined]
                transitions[key].update(values)
        # Update "state" class attributes
        for key, value in m_states.items():
            setattr(cls, key, frozenset(value))
        for state in transitions.keys():
            setattr(cls, state, state)
        cls.TRANSITIONS = transitions
        super().__init__(name, bases, cls_dict)


class StateEnum(metaclass=StateEnumMetaclass):
    """Base class for state enumerations with transition rules."""

    #: Every state, the keys of ``TRANSITIONS``.
    ALL_STATES: ClassVar[frozenset[str]]

    #: The states no transition leaves.
    FINAL_STATES: ClassVar[frozenset[str]]

    #: Each state, mapped to the states having a transition to it.
    INVERSE_TRANSITIONS: ClassVar[dict[str, frozenset[str]]]

    #: Each state, mapped to the states it has a transition to. Declared by each subclass.
    TRANSITIONS: ClassVar[Mapping[str, Collection[str]]]

    @classmethod
    def get(cls, name: str) -> str | frozenset[str] | None:
        """Return the state or state set matching a lowercase name."""
        if name.lower() == name:
            if (name := name.upper()) in cls.ALL_STATES:
                return name
            return getattr(cls, name + '_STATES', None)
        return None

    @classmethod
    def get_transit_from(
        cls,
        state: str,
        *,
        auto_inverse: bool = False,
    ) -> frozenset[str] | tuple[frozenset[str], bool]:
        """
        Return the states having a transition to *state*.

        With ``auto_inverse``, return the smaller of two sets instead, paired with whether it holds
        the states having a transition to *state*:

        * (the states having a transition to *state*, ``True``)
        * (the states having none, ``False``)
        """
        valid = cls.INVERSE_TRANSITIONS[state]
        if not auto_inverse:
            return valid
        not_valid = cls.ALL_STATES - valid
        return (not_valid, False) if len(valid) > len(not_valid) else (valid, True)
