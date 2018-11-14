# -*- encoding: utf-8 -*-

"""
Abstract models for building your own models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import models

from pytoolbox import module

from . import fields

_all = module.All(globals())


class Timestamped(models.Model):

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('created_at', 'updated_at')

    created_at = fields.CreatedAtField()
    updated_at = fields.UpdatedAtField()


__all__ = _all.diff(globals())
