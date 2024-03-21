from __future__ import annotations

import re

__all__ = ['DEFFERED_REGEX']

DEFFERED_REGEX = re.compile(r'_.*')
