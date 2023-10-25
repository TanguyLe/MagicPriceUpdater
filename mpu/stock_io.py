import base64
import gzip
import io
from pathlib import Path

import pandas as pd

from mpu.excel_formats import (STOCK_COLUMNS_FORMAT,
                               STOCK_WITH_NEW_PRICE_COLUMNS_FORMAT)
from mpu.utils.pyopenxl_utils import EXCEL_ENGINE, format_excel_df


def get_stock_file_path(folder_path: Path, csv: bool = False) -> Path:
    """Constructs the stock file path from a folder path"""
    if csv:
        return folder_path / "stock.csv"
    else:
        return folder_path / "stock.xlsx"


def convert_base64_gzipped_string_to_dataframe(b64_zipped_string: str) -> pd.DataFrame:
    """Converts a base64 gzipped strings (or bytes) into a pandas dataframe"""
    decoded_string = base64.b64decode(b64_zipped_string)
    csv_string = gzip.decompress(decoded_string)

    return pd.read_csv(io.BytesIO(csv_string), sep=";")


def save_stock_df_as_excel_formatted_file(
    df: pd.DataFrame, file_path: Path, new_price: bool = False
) -> None:
    cols_format = (
        STOCK_WITH_NEW_PRICE_COLUMNS_FORMAT if new_price else STOCK_COLUMNS_FORMAT
    )

    with pd.ExcelWriter(path=str(file_path), engine=EXCEL_ENGINE) as writer:
        df.to_excel(excel_writer=writer, index=False, engine=EXCEL_ENGINE)

        format_excel_df(df=df, writer=writer, format_config=cols_format)
