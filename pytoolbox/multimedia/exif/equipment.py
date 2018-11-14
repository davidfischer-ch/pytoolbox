# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import abc, re

from pytoolbox import module

_all = module.All(globals())


class Equipement(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, metadata):
        self.metadata = metadata

    def __bool__(self):
        return bool(self.model)

    def __eq__(self, other):
        try:
            return self.brand == other.brand and self.model == other.model
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return '<{0.__class__.__name__} {0.brand} {0.model}>'.format(self)

    @abc.abstractproperty
    def brand(self):
        pass

    @property
    def model(self):
        if self.brand and self._model:
            return re.sub('{0.brand}\s+'.format(self), '', self._model, 1, re.IGNORECASE)
        return self._model

    @abc.abstractproperty
    def _model(self):
        pass

    @abc.abstractproperty
    def tags(self):
        pass

    def refresh(self):
        self.__dict__.pop('tags', None)


__all__ = _all.diff(globals())
