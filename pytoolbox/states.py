# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import collections, inspect

from . import module

_all = module.All(globals())


class StateEnumMetaclass(type):

    def __init__(self, name, bases, cls_dict):
        super(StateEnumMetaclass, self).__init__(name, bases, cls_dict)
        if hasattr(self, 'TRANSITIONS'):
            self.ALL_STATES = frozenset(self.TRANSITIONS.iterkeys())
            self.FINAL_STATES = frozenset(s for s, t in self.TRANSITIONS.iteritems() if not t)
            inverse_transitions = collections.defaultdict(set)
            for state, transitions in self.TRANSITIONS.iteritems():
                set(inverse_transitions[t].add(state) for t in transitions)
            self.INVERSE_TRANSITIONS = {s: frozenset(t) for s, t in inverse_transitions.iteritems()}


class StateEnumMergeMetaclass(StateEnumMetaclass):

    def __init__(self, name, bases, cls_dict):
        # Retrieve base "state" classes attributes
        m_states, transitions = collections.defaultdict(set), collections.defaultdict(set)
        for base in bases:
            for key, value in (i for i in inspect.getmembers(base) if i[0].endswith('_STATES')):
                m_states[key].update(value)
            for key, values in base.TRANSITIONS.iteritems():
                transitions[key].update(values)
        # Update "state" class attributes
        for key, value in m_states.iteritems():
            setattr(self, key, frozenset(value))
        for state in transitions.iterkeys():
            setattr(self, state, state)
        self.TRANSITIONS = transitions
        super(StateEnumMergeMetaclass, self).__init__(name, bases, cls_dict)


class StateEnum(object):

    __metaclass__ = StateEnumMetaclass

    @classmethod
    def get(cls, name):
        if name.lower() == name:
            name = name.upper()
            if name in cls.ALL_STATES:
                return name
            return getattr(cls, name + '_STATES', None)

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
