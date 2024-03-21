"""
Extra widgets for your forms.
"""
from __future__ import annotations

from django.forms import widgets
from django.utils.html import mark_safe

__all__ = ['CalendarDateInput', 'ClockTimeInput']


class CalendarDateInput(widgets.DateInput):
    def render(self, *args, **kwargs):
        html = super().render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append date">'
            f'{html}<span class="add-on"><i class="icon-calendar"></i></span></div>')


class ClockTimeInput(widgets.TimeInput):
    def render(self, *args, **kwargs):
        html = super().render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append bootstrap-timepicker">'
            f'{html}<span class="add-on"><i class="icon-time"></i></span></div>')
