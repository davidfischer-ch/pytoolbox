"""
Pandas helpers for reading ODS files and building dictionaries from DataFrames.
"""

from __future__ import annotations

import ezodf
import pandas as pd


def map_dict(df: pd.DataFrame, key_column: str, value_column: str, *, dropna: bool = True) -> dict:
    """Build a dictionary mapping *key_column* to *value_column* from a DataFrame."""
    df = df[[key_column, value_column]]
    if dropna:
        df = df.dropna()
    return df.set_index(key_column)[value_column].to_dict()


def read_ods(filename: str, sheet_no: int, *, header_pos: int = 0) -> pd.DataFrame:
    """Read an ODS spreadsheet sheet into a :class:`~pandas.DataFrame`."""
    tab = ezodf.opendoc(filename=filename).sheets[sheet_no]
    return pd.DataFrame(
        {
            col[header_pos].value: [cell.value for cell in col[header_pos + 1 :]]
            for col in tab.columns()
        }
    )
