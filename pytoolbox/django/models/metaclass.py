"""
Meta-classes for enhancing your models.
"""
from __future__ import annotations

import abc

from django.db import models

_all__ = ['ABCModelMeta']


class ABCModelMeta(abc.ABCMeta, type(models.Model)):
    """
    Meta-class for building an abstract Model with abstract methods, properties, ...

    **Example usage**

    >> class AbstractModel(models.Model):
    .. __metaclass__ = AbstractModelMeta
    ..
    .. class Meta:
    ..     abstract = True
    """
