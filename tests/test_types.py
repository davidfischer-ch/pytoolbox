# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import copy

from pytoolbox import types

from . import base


class TestTypes(base.TestCase):

    tags = ('types', )

    def test_Missing(self):
        self.equal('{0}'.format(types.Missing), 'Missing')
        self.false(bool(types.Missing))
        self.is_missing(copy.copy(types.Missing))
        self.is_missing(copy.deepcopy(types.Missing))
