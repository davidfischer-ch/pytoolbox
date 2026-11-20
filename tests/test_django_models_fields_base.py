"""Tests for the django.models.fields.base module."""

from __future__ import annotations

from decimal import Decimal

from pytoolbox.django.models.fields import base

# --- MoneyField -----------------------------------------------------------------------------------


def test_money_field_clone_keeps_the_decimal_places() -> None:
    """The field a migration rebuilds has the precision and the digits of the declared one."""
    field = base.MoneyField(1000, decimal_places=4)
    _, _, args, kwargs = field.deconstruct()

    clone = base.MoneyField(*args, **kwargs)

    assert (clone.decimal_places, clone.max_digits) == (4, field.max_digits)


def test_money_field_holds_its_max_value_whatever_the_decimal_places() -> None:
    """The digits left before the decimal point are enough for the max value."""
    field = base.MoneyField(1000, decimal_places=4)

    assert field.clean(Decimal('1000.0000'), None) == Decimal('1000.0000')
