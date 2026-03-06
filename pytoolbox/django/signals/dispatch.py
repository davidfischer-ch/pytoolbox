"""
Custom signal classes for Django.
"""
from __future__ import annotations

from django import dispatch as _dispatch

from pytoolbox.django.models import utils as _utils

__all__ = ['InstanceSignal', 'post_state_transition']


class InstanceSignal(_dispatch.Signal):
    """Signal that resolves the sender to the base model of the given instance."""

    def send(self, sender: type | None = None, **named: object) -> list[tuple[object, object]]:
        """Send signal using the base model as sender."""
        return super().send(_utils.get_base_model(sender or named['instance']), **named)

    def send_robust(
            self,
            sender: type | None = None,
            **named: object
    ) -> list[tuple[object, object]]:
        """Send signal robustly using the base model as sender."""
        return super().send(_utils.get_base_model(sender or named['instance']), **named)


post_state_transition = InstanceSignal()
