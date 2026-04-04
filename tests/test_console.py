"""Tests for the console module."""

from __future__ import annotations

import io
import os
import sys
from unittest.mock import patch

import termcolor

from pytoolbox import console


def test_toggle_colors() -> None:
    """Sets FORCE_COLOR for colorize=True and NO_COLOR for colorize=False, exclusively."""
    assert 'FORCE_COLOR' in console.toggle_colors(colorize=True)
    assert 'NO_COLOR' not in console.toggle_colors(colorize=True)
    assert 'NO_COLOR' in console.toggle_colors(colorize=False)
    assert 'FORCE_COLOR' not in console.toggle_colors(colorize=False)


def test_disable_colors_with_termcolor() -> None:
    """NO_COLOR environment variable makes termcolor output plain text."""
    with patch.dict(os.environ, console.toggle_colors(colorize=False), clear=True):
        termcolor.can_colorize.cache_clear()
        assert termcolor.colored('test', 'green') == 'test'


def test_enable_colors_with_termcolor() -> None:
    """FORCE_COLOR environment variable makes termcolor emit ANSI escape codes."""
    with patch.dict(os.environ, console.toggle_colors(colorize=True), clear=True):
        termcolor.can_colorize.cache_clear()
        assert termcolor.colored('test', 'green') == '\x1b[32mtest\x1b[0m'


# confirm() tests -------------------------------------------------------


def test_confirm_default_true_empty_input() -> None:
    """confirm() returns True when default=True and user presses Enter."""
    stream = io.StringIO()
    with patch('builtins.input', return_value=''):
        assert console.confirm('Continue', default=True, stream=stream) is True
    assert 'Y/n' in stream.getvalue()


def test_confirm_default_false_empty_input() -> None:
    """confirm() returns False when default=False and user presses Enter."""
    stream = io.StringIO()
    with patch('builtins.input', return_value=''):
        assert console.confirm('Continue', default=False, stream=stream) is False
    assert 'y/N' in stream.getvalue()


def test_confirm_yes_input() -> None:
    """confirm() returns True when user types 'y'."""
    with patch('builtins.input', return_value='y'):
        assert console.confirm(stream=io.StringIO()) is True


def test_confirm_no_input() -> None:
    """confirm() returns False when user types 'no'."""
    with patch('builtins.input', return_value='no'):
        assert console.confirm(stream=io.StringIO()) is False


def test_confirm_invalid_then_valid_input() -> None:
    """confirm() re-prompts on invalid input then accepts valid answer."""
    stream = io.StringIO()
    with patch('builtins.input', side_effect=['maybe', 'yes']):
        assert console.confirm(stream=stream) is True
    assert 'please enter y(es) or n(o).' in stream.getvalue()


# choice() tests ---------------------------------------------------------


def test_choice_valid_input() -> None:
    """choice() returns the selected option immediately."""
    with patch('builtins.input', return_value='blue'):
        result = console.choice(
            'Favorite color?',
            choices=['blue', 'red'],
            stream=io.StringIO(),
        )
    assert result == 'blue'


def test_choice_no_question() -> None:
    """choice() without question text shows choices in brackets."""
    with patch('builtins.input', return_value='a'):
        result = console.choice(choices=['a', 'b'], stream=io.StringIO())
    assert result == 'a'


def test_choice_invalid_then_valid() -> None:
    """choice() re-prompts when given an invalid answer."""
    stream = io.StringIO()
    with patch('builtins.input', side_effect=['green', 'red']):
        result = console.choice(
            'Color?',
            choices=['blue', 'red'],
            stream=stream,
        )
    assert result == 'red'
    assert 'Please choose between' in stream.getvalue()


# print_error() tests ----------------------------------------------------


def test_print_error_with_exit() -> None:
    """print_error() writes message and calls sys.exit with given code."""
    stream = io.StringIO()
    with patch.object(sys, 'exit', side_effect=SystemExit(2)) as mock_exit:
        try:
            console.print_error('boom', exit_code=2, stream=stream)
        except SystemExit:
            pass
    assert '[ERROR] boom' in stream.getvalue()
    mock_exit.assert_called_once_with(2)


def test_print_error_no_exit() -> None:
    """print_error() with exit_code=None does not call sys.exit."""
    stream = io.StringIO()
    console.print_error('warning', exit_code=None, stream=stream)
    assert '[ERROR] warning' in stream.getvalue()


# progress_bar() tests ---------------------------------------------------


def test_progress_bar_writes_correct_bar() -> None:
    """progress_bar() renders done/todo portions at correct ratio."""
    stream = io.StringIO()
    console.progress_bar(
        start_time=0.0,
        current=5,
        total=10,
        size=10,
        template='[{done}{todo}]',
        stream=stream,
    )
    assert stream.getvalue() == '[=====     ]'


def test_progress_bar_zero_total() -> None:
    """progress_bar() with total=0 writes nothing (avoids division by zero)."""
    stream = io.StringIO()
    console.progress_bar(
        start_time=0.0,
        current=0,
        total=0,
        template='[{done}{todo}]',
        stream=stream,
    )
    assert stream.getvalue() == ''


# set_columns() tests ----------------------------------------------------


def test_set_columns_explicit_value() -> None:
    """set_columns() sets COLUMNS env var to the given value."""
    result = console.set_columns(80)
    assert result == 80
    assert os.environ['COLUMNS'] == '80'


def test_set_columns_auto() -> None:
    """set_columns() without value uses terminal size or default."""
    result = console.set_columns()
    assert isinstance(result, int)
    assert os.environ['COLUMNS'] == str(result)
