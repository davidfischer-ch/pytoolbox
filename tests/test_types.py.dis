import copy

from pytoolbox import types

from . import base


class TestTypes(base.TestCase):

    tags = ('types', )

    def test_Missing(self):
        self.equal(f'{types.Missing}', 'Missing')
        self.false(bool(types.Missing))
        self.is_missing(copy.copy(types.Missing))
        self.is_missing(copy.deepcopy(types.Missing))
