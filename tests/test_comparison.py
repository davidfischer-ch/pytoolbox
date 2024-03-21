# pylint:disable=too-few-public-methods
from __future__ import annotations

import os
from unittest.mock import patch

from pytest import mark

from pytoolbox import comparison, console


class Point2D(comparison.SlotsEqualityMixin):

    __slots__ = ('x', 'y', 'name')

    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name


class Point2Dv2(Point2D):
    pass


class Point3D(comparison.SlotsEqualityMixin):

    __slots__ = ('x', 'y', 'z', 'name')

    def __init__(self, x, y, z, name):
        self.x = x
        self.y = y
        self.z = z
        self.name = name


def test_equality_same_class() -> None:
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point2D(10, -3, 'dot')
    point_3 = Point2D(10, -4, 'dot')
    if not (point_1 == point_2 and point_1 != point_3):
        raise ValueError()


def test_equality_inheritance() -> None:
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point2Dv2(10, -3, 'dot')
    point_3 = Point2Dv2(10, -4, 'dot')
    if not (point_1 == point_2 and point_1 != point_3):
        raise AssertionError()


def test_equality_different_class() -> None:
    point_1 = Point2D(10, -3, 'dot')
    point_2 = Point3D(10, -3, 5, 'dot')
    point_3 = Point3D(10, -4, 2, 'dot')
    if point_1 in (point_2, point_3):
        raise AssertionError()


# Content ------------------------------------------------------------------------------------------

def test_unified_diff() -> None:
    assert comparison.unified_diff(
        'Some T',
        'Other T',
        fromfile='a.py',
        tofile='b.py',
        colorize=False) == ("""
--- a.py

+++ b.py

@@ -1 +1 @@

-Some T
+Other T
""").strip()


def test_unified_diff_colorize() -> None:
    with patch.dict(os.environ, console.toggle_colors(colorize=True), clear=True):
        assert comparison.unified_diff(
            'Some T',
            'Other T',
            fromfile='a.py',
            tofile='b.py',
            colorize=True) == ("""
\x1b[31m--- a.py
\x1b[0m
\x1b[32m+++ b.py
\x1b[0m
@@ -1 +1 @@

\x1b[31m-Some T\x1b[0m
\x1b[32m+Other T\x1b[0m
""").strip()


# Versions -----------------------------------------------------------------------------------------

@mark.parametrize(('version_a', 'version_b', 'operation', 'expected'), [
    ('master', 'master', '<', False),
    ('master', 'master', '<=', True),
    ('master', 'master', '==', True),
    ('master', 'master', '!=', False),
    ('master', 'master', '>=', True),
    ('master', 'master', '>', False),

    ('master', 'main', '<', None),
    ('master', 'main', '<=', None),
    ('master', 'main', '==', False),
    ('master', 'main', '!=', True),
    ('master', 'main', '>=', None),
    ('master', 'main', '>', None),

    ('v4.10', 'v4.10', '<', False),
    ('v4.10', 'v4.10', '<=', True),
    ('v4.10', 'v4.10', '==', True),
    ('v4.10', 'v4.10', '!=', False),
    ('v4.10', 'v4.10', '>=', True),
    ('v4.10', 'v4.10', '>', False),

    ('v4.10', 'v4.11', '<', True),
    ('v4.10', 'v4.11', '<=', True),
    ('v4.10', 'v4.11', '==', False),
    ('v4.10', 'v4.11', '!=', True),
    ('v4.10', 'v4.11', '>=', False),
    ('v4.10', 'v4.11', '>', False),

    ('v4.10', 'v4.10.1', '<', True),
    ('v4.10', 'v4.10.1', '<=', True),
    ('v4.10', 'v4.10.1', '==', False),
    ('v4.10', 'v4.10.1', '!=', True),
    ('v4.10', 'v4.10.1', '>=', False),
    ('v4.10', 'v4.10.1', '>', False),

    ('v4.10', 'master', '<', None),
    ('v4.10', 'master', '<=', None),
    ('v4.10', 'master', '==', None),
    ('v4.10', 'master', '!=', None),
    ('v4.10', 'master', '>=', None),
    ('v4.10', 'master', '>', None),

    # Comparison to a commit is not possible
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '<', None),
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '<=', None),
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '==', None),
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '!=', None),
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '>=', None),
    ('3.1', 'db37a6c036b348439fee5a58cef57287948e32fb', '>', None),

    # Caution
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '<', None),
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '<=', None),
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '==', False),
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '!=', True),
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '>=', None),
    ('master', 'db37a6c036b348439fee5a58cef57287948e32fb', '>', None),
])
def test_compare_versions(version_a, version_b, operation, expected) -> None:
    assert comparison.compare_versions(version_a, version_b, operation) == expected
