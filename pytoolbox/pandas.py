import ezodf, pandas as pd


def map_dict(df, key_column, value_column, dropna=True):
    df = df[[key_column, value_column]]
    if dropna:
        df = df.dropna()
    return df.set_index(key_column)[value_column].to_dict()


def read_ods(filename, sheet_no, header_pos=0):
    tab = ezodf.opendoc(filename=filename).sheets[sheet_no]
    return pd.DataFrame({
        col[header_pos].value: [cell.value for cell in col[header_pos + 1:]]
        for col in tab.columns()
    })
