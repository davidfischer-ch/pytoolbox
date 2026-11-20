"""
Django core constants.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = ['DEFERRED_PATTERN']

#: Regex matching deferred field attribute names.
DEFERRED_PATTERN: Final[re.Pattern[str]] = re.compile(r'_.*')
