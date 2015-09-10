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
Meta-classes for enhancing your models.
"""

import abc
from django.db import models

from ... import module

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
