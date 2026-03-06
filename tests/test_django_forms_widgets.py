from __future__ import annotations

from pytoolbox.django.forms import widgets


def test_calendar_date_input_render() -> None:
    """CalendarDateInput wraps the inner HTML with a calendar icon add-on."""
    widget = widgets.CalendarDateInput()
    html = widget.render('date', '2025-01-01')
    assert 'input-append date' in html
    assert 'icon-calendar' in html
    assert 'date' in html


def test_clock_time_input_render() -> None:
    """ClockTimeInput wraps the inner HTML with a clock icon add-on."""
    widget = widgets.ClockTimeInput()
    html = widget.render('time', '12:00')
    assert 'input-append bootstrap-timepicker' in html
    assert 'icon-time' in html
    assert 'time' in html
