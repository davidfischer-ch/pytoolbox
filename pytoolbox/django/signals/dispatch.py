"""
Custom signal classes for Django.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django import dispatch as _dispatch
from django.db import models

from pytoolbox.compat import override
from pytoolbox.django.models import utils as _utils

__all__ = ['InstanceSignal', 'post_state_transition']


class InstanceSignal(_dispatch.Signal):
    """Signal that resolves the sender to the base model of the given instance."""

    @override
    def send(
        self,
        sender: type[models.Model] | None = None,
        **named: Any,
    ) -> list[tuple[Callable[..., Any], str | None]]:
        """Send signal using the base model as sender."""
        return super().send(_utils.get_base_model(sender or named['instance']), **named)

    @override
    def send_robust(
        self,
        sender: type[models.Model] | None = None,
        **named: Any,
    ) -> list[tuple[Callable[..., Any], Exception | Any]]:
        """Send signal robustly using the base model as sender."""
        return super().send_robust(_utils.get_base_model(sender or named['instance']), **named)


post_state_transition = InstanceSignal()
