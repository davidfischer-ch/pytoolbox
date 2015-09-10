# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#  Origin         : https://github.com/davidfischer-ch/pytoolbox.git
#
#**********************************************************************************************************************#

from __future__ import absolute_import, division, print_function, unicode_literals

"""
Mix-ins for building your own model managers.
"""

from ..query import mixins as query_mixins
from .... import module

_all = module.All(globals())

AtomicGetUpdateOrCreateMixin = query_mixins.AtomicGetUpdateOrCreateMixin
AtomicGetRestoreOrCreateMixin = query_mixins.AtomicGetRestoreOrCreateMixin
CreateModelMethodMixin = query_mixins.CreateModelMethodMixin
RelatedModelMixin = query_mixins.RelatedModelMixin
StateMixin = query_mixins.StateMixin

__all__ = _all.diff(globals())
