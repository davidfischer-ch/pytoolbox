"""
Django core constants.
"""
from __future__ import annotations

from typing import Final
import re

__all__ = ['DEFFERED_REGEX']

#: Regex matching deferred field attribute names.
DEFFERED_REGEX: Final[re.Pattern[str]] = re.compile(r'_.*')
