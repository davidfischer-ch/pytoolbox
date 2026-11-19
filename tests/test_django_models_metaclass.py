"""Tests for the model meta-classes."""

# pylint:disable=too-few-public-methods
from __future__ import annotations

import abc

import pytest
from django.db import models

from pytoolbox.django.models.metaclass import ABCModelMeta


def test_a_model_missing_an_abstract_method_cannot_be_instantiated() -> None:
    """A concrete model left without an abstract method of its base raises on instantiation."""

    class Named(models.Model, metaclass=ABCModelMeta):
        """An abstract model requiring a name."""

        class Meta:
            """Abstract, under the test application."""

            abstract = True
            app_label = 'test'

        @abc.abstractmethod
        def get_name(self) -> str:
            """Return the name."""

    class Anonymous(Named):  # pylint:disable=abstract-method
        """A concrete model not defining the name."""

        class Meta:
            """Under the test application."""

            app_label = 'test'

    class Person(Named):
        """A concrete model defining the name."""

        class Meta:
            """Under the test application."""

            app_label = 'test'

        def get_name(self) -> str:
            """Return a fixed name."""
            return 'Alice'

    with pytest.raises(TypeError, match='get_name'):
        Anonymous()
    assert Person().get_name() == 'Alice'
