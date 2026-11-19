"""
Meta-classes for enhancing your models.
"""

from __future__ import annotations

import abc

from django.db import models

__all__ = ['ABCModelMeta']


class ABCModelMeta(abc.ABCMeta, type(models.Model)):
    """
    Meta-class for building an abstract Model with abstract methods, properties, ...

    **Example usage**

    >>> class Named(models.Model, metaclass=ABCModelMeta):
    ...     class Meta:
    ...         abstract = True
    ...
    ...     @abc.abstractmethod
    ...     def get_name(self) -> str: ...
    """
