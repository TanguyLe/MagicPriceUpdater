import base64
import gzip
import io
from pathlib import Path

import pandas as pd

from mpu.pyopenxl_utils import format_and_save_df, EXCEL_ENGINE

COLUMNS_FORMAT = {
    "idArticle": {"hidden": True},
    "Local Name": {"hidden": True},
    "English Name": {"width": 7.5},
    "Exp. Name": {"hidden": True},
    "Signed?": {"hidden": True},
    "Playset?": {"hidden": True},
    "Altered?": {"hidden": True},
    "idCurrency": {"hidden": True},
    "Currency Code": {"hidden": True},
    "Price": {"color": "949494E8"},
    "SuggestedPrice": {"color": "949494E8"},
    "PriceApproval": {"color": "FFF0F8FF"},
}


def get_stock_file_path(folder_path: Path) -> Path:
    """Constructs the stock file path from a folder path"""
    return folder_path / "stock.xlsx"


def convert_base64_gzipped_string_to_dataframe(b64_zipped_string: str) -> pd.DataFrame:
    """Converts a base64 gzipped strings (or bytes) into a pandas dataframe"""
    decoded_string = base64.b64decode(b64_zipped_string)
    csv_string = gzip.decompress(decoded_string)

    return pd.read_csv(io.BytesIO(csv_string), sep=";")


def save_stock_df_as_excel_formatted_file(df: pd.DataFrame, file_path: Path) -> None:
    writer = pd.ExcelWriter(path=str(file_path), engine=EXCEL_ENGINE)
    df.to_excel(excel_writer=writer, index=False, engine=EXCEL_ENGINE)

    format_and_save_df(df=df, writer=writer, format_config=COLUMNS_FORMAT)
