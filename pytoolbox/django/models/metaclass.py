# -*- encoding: utf-8 -*-

"""
Meta-classes for enhancing your models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import abc

from django.db import models

from pytoolbox import module

_all = module.All(globals())


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


__all__ = _all.diff(globals())
