"""
Django core constants.
"""
from __future__ import annotations

import re

__all__ = ['DEFFERED_REGEX']

#: Regex matching deferred field attribute names.
DEFFERED_REGEX = re.compile(r'_.*')
