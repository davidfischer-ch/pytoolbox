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
Abstract models for building your own models.
"""

from django.db import models

from . import fields
from ... import module

_all = module.All(globals())


class Timestamped(models.Model):

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('created_at', 'updated_at')

    created_at = fields.CreatedAtField()
    updated_at = fields.UpdatedAtField()

__all__ = _all.diff(globals())
