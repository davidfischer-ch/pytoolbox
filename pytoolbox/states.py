from __future__ import annotations

from typing import Any
import collections
import inspect

__all__ = ['StateEnumMetaclass', 'StateEnumMergeMetaclass', 'StateEnum']


class StateEnumMetaclass(type):

    # TODO type hint class attributes?

    def __init__(cls, name: str, bases: tuple[type, ...], cls_dict: dict[str, Any]) -> None:
        super().__init__(name, bases, cls_dict)
        if hasattr(cls, 'TRANSITIONS'):
            cls.ALL_STATES = frozenset(cls.TRANSITIONS.keys())
            cls.FINAL_STATES = frozenset(s for s, t in cls.TRANSITIONS.items() if not t)
            inverse_transitions = collections.defaultdict(set)
            for state, transitions in cls.TRANSITIONS.items():
                for transition in transitions:
                    inverse_transitions[transition].add(state)
            cls.INVERSE_TRANSITIONS = {s: frozenset(t) for s, t in inverse_transitions.items()}


class StateEnumMergeMetaclass(StateEnumMetaclass):

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


class StateEnum(object, metaclass=StateEnumMetaclass):

    # TODO type hint class attributes?

    @classmethod
    def get(cls, name: str):  # TODO return type hint
        if name.lower() == name:
            if (name := name.upper()) in cls.ALL_STATES:
                return name
            return getattr(cls, name + '_STATES', None)
        return None

    @classmethod
    def get_transit_from(cls, state: str, *, auto_inverse: bool = False):  # TODO return type hint
        """
        Return a set with the states having a transition to given `state`.

        If `auto_inverse` is set to True then a tuple is returned containing the smallest set from:

        * (States allowed to transit to given `state`, True)
        * (States not allowed to transit to given `state`, False)
        """
        valid = cls.INVERSE_TRANSITIONS[state]
        if not auto_inverse:
            return valid
        not_valid = cls.ALL_STATES - valid
        return (not_valid, False) if len(valid) > len(not_valid) else (valid, True)
