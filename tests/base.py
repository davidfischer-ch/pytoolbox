import unittest

from pytoolbox.unittest import FilterByTagsMixin, MissingMixin, SnakeCaseMixin

__all__ = ['TestCase']


class TestCase(FilterByTagsMixin, MissingMixin, SnakeCaseMixin, unittest.TestCase):
    pass
