"""
Extra widgets for your forms.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import Any

from django.forms import widgets
from django.forms.renderers import BaseRenderer
from django.utils.safestring import SafeString, mark_safe

from pytoolbox.compat import override

__all__ = ['CalendarDateInput', 'ClockTimeInput']


class CalendarDateInput(widgets.DateInput):
    """Date input widget wrapped with a calendar icon add-on."""

    @override
    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
        renderer: BaseRenderer | None = None,
    ) -> SafeString:
        """Render the date input with a calendar icon add-on."""
        html = super().render(name, value, attrs, renderer)
        return mark_safe(
            '<div class="input-append date">'
            f'{html}<span class="add-on"><i class="icon-calendar"></i></span></div>',
        )


class ClockTimeInput(widgets.TimeInput):
    """Time input widget wrapped with a clock icon add-on."""

    @override
    def render(
        self,
        name: str,
        value: Any,
        attrs: dict[str, Any] | None = None,
        renderer: BaseRenderer | None = None,
    ) -> SafeString:
        """Render the time input with a clock icon add-on."""
        html = super().render(name, value, attrs, renderer)
        return mark_safe(
            '<div class="input-append bootstrap-timepicker">'
            f'{html}<span class="add-on"><i class="icon-time"></i></span></div>',
        )
