from __future__ import annotations

import os
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
