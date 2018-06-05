# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from pytoolbox.unittest import FilterByTagsMixin, MissingMixin, SnakeCaseMixin

__all__ = ('TestCase', )


class TestCase(FilterByTagsMixin, MissingMixin, SnakeCaseMixin, unittest.TestCase):
    pass
