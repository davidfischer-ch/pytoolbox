"""
Typing constructs bridged across the Python versions pytoolbox supports.

``typing.override`` landed in Python 3.12; on 3.11 it comes from ``typing_extensions``, which is a
conditional dependency. Importing it from here keeps the version gate in one place instead of
repeating it in every module that marks an override.
"""

import sys

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

__all__ = ['override']
