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
Decorators for enhancing your serializers.
"""

from . import mixins
from ... import module

_all = module.All(globals())


def read_only():
    def _read_only(serializer):
        serializer.__bases__ = (mixins.ReadOnlyMixin, ) + serializer.__bases__
        serializer.Meta.read_only_fields = serializer.Meta.fields
        for field in serializer._declared_fields.values():
            field.read_only = True
        return serializer
    return _read_only

__all__ = _all.diff(globals())
