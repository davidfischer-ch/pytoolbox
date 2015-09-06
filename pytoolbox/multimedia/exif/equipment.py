# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import abc, re

from ... import module

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
