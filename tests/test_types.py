from __future__ import annotations

import copy

from pytoolbox import types


def test_missing() -> None:
    assert f'{types.Missing}' == 'Missing'
    assert types.Missing is not False
    assert bool(types.Missing) is False
    assert copy.copy(types.Missing) is types.Missing
    assert copy.deepcopy(types.Missing) is types.Missing
