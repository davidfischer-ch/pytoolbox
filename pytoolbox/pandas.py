"""
Pandas helpers for reading ODS files and building dictionaries from DataFrames.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def map_dict(df: pd.DataFrame, key_column: str, value_column: str, *, dropna: bool = True) -> dict:
    """Build a dictionary mapping *key_column* to *value_column* from a DataFrame."""
    df = df[[key_column, value_column]]
    if dropna:
        df = df.dropna()
    return df.set_index(key_column)[value_column].to_dict()


def read_ods(filename: str, sheet_no: int, *, header_pos: int = 0) -> pd.DataFrame:
    """
    Read a sheet of an ODS spreadsheet, its header at row *header_pos*, into a DataFrame.

    The file is opened locally: a URL is the name of a missing file, never fetched by pandas.
    """
    with Path(filename).open('rb') as f:
        return pd.read_excel(f, engine='odf', header=header_pos, sheet_name=sheet_no)
