"""
Extra widgets for your forms.
"""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from django.forms import widgets
from django.utils.html import mark_safe

__all__ = ['CalendarDateInput', 'ClockTimeInput']


class CalendarDateInput(widgets.DateInput):
    """Date input widget wrapped with a calendar icon add-on."""

    def render(self, *args: object, **kwargs: object) -> str:
        """Render the date input with a calendar icon add-on."""
        html = super().render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append date">'
            f'{html}<span class="add-on"><i class="icon-calendar"></i></span></div>',
        )


class ClockTimeInput(widgets.TimeInput):
    """Time input widget wrapped with a clock icon add-on."""

    def render(self, *args: object, **kwargs: object) -> str:
        """Render the time input with a clock icon add-on."""
        html = super().render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append bootstrap-timepicker">'
            f'{html}<span class="add-on"><i class="icon-time"></i></span></div>',
        )
