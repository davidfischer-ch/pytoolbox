"""
Abstract models for building your own models.
"""
from __future__ import annotations

from django.db import models

from . import fields

__all__ = ['Timestamped']


class Timestamped(models.Model):

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ('created_at', 'updated_at')

    created_at = fields.CreatedAtField()
    updated_at = fields.UpdatedAtField()
