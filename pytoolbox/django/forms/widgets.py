# -*- encoding: utf-8 -*-

"""
Extra widgets for your forms.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.forms import widgets
from django.utils.html import mark_safe

from pytoolbox import module

_all = module.All(globals())


class CalendarDateInput(widgets.DateInput):
    def render(self, *args, **kwargs):
        html = super(CalendarDateInput, self).render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append date">'
            '{0}<span class="add-on"><i class="icon-calendar"></i></span></div>'.format(html))


class ClockTimeInput(widgets.TimeInput):
    def render(self, *args, **kwargs):
        html = super(ClockTimeInput, self).render(*args, **kwargs)
        return mark_safe(
            '<div class="input-append bootstrap-timepicker">'
            '{0}<span class="add-on"><i class="icon-time"></i></span></div>'.format(html))


__all__ = _all.diff(globals())
