from __future__ import annotations

import os
from unittest.mock import patch

import termcolor

from pytoolbox import console


def test_toggle_colors() -> None:
    assert 'FORCE_COLOR' in console.toggle_colors(colorize=True)
    assert 'NO_COLOR' not in console.toggle_colors(colorize=True)
    assert 'NO_COLOR' in console.toggle_colors(colorize=False)
    assert 'FORCE_COLOR' not in console.toggle_colors(colorize=False)


def test_disable_colors_with_termcolor() -> None:
    with patch.dict(os.environ, console.toggle_colors(colorize=False), clear=True):
        assert termcolor.colored('test', 'green') == 'test'


def test_enable_colors_with_termcolor() -> None:
    with patch.dict(os.environ, console.toggle_colors(colorize=True), clear=True):
        assert termcolor.colored('test', 'green') == '\x1b[32mtest\x1b[0m'
