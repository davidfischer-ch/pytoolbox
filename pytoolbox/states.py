import collections, inspect

from . import module

_all = module.All(globals())


class StateEnumMetaclass(type):

    def __init__(cls, name, bases, cls_dict):
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

    def __init__(cls, name, bases, cls_dict):
        # Retrieve base "state" classes attributes
        m_states, transitions = collections.defaultdict(set), collections.defaultdict(set)
        for base in bases:
            for key, value in (i for i in inspect.getmembers(base) if i[0].endswith('_STATES')):
                m_states[key].update(value)
            for key, values in base.TRANSITIONS.items():
                transitions[key].update(values)
        # Update "state" class attributes
        for key, value in m_states.items():
            setattr(cls, key, frozenset(value))
        for state in transitions.keys():
            setattr(cls, state, state)
        cls.TRANSITIONS = transitions
        super().__init__(name, bases, cls_dict)


class StateEnum(object, metaclass=StateEnumMetaclass):

    @classmethod
    def get(cls, name):
        if name.lower() == name:
            name = name.upper()
            if name in cls.ALL_STATES:
                return name
            return getattr(cls, name + '_STATES', None)
        return None

    @classmethod
    def get_transit_from(cls, state, auto_inverse=False):
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


__all__ = _all.diff(globals())
