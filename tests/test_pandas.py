"""Tests for the pandas module."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from pytoolbox import pandas as pytoolbox_pandas

SHEETS_ODS: Final[Path] = Path(__file__).parent / 'data' / 'sheets.ods'


def test_read_ods_reads_a_sheet_by_number() -> None:
    """A sheet is read by its number, an empty cell as NaN."""
    pd.testing.assert_frame_equal(
        pytoolbox_pandas.read_ods(str(SHEETS_ODS), 0),
        pd.DataFrame({'name': ['apple', 'pear'], 'count': [3.0, None]}),
    )


def test_read_ods_reads_the_header_at_its_row() -> None:
    """The rows above the header row are skipped, whole numbers read as integers."""
    pd.testing.assert_frame_equal(
        pytoolbox_pandas.read_ods(str(SHEETS_ODS), 1, header_pos=1),
        pd.DataFrame({'name': ['nail', 'screw'], 'count': [120, 40], 'ratio': [0.5, 0.25]}),
    )
