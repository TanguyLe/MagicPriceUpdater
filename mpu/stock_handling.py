import base64
import gzip
import io
import string
from pathlib import Path
from typing import NamedTuple

import pandas as pd
from openpyxl.styles import PatternFill


class BasicStats(NamedTuple):
    total_current_price: float
    total_suggested_price: float
    relative_diff: float


HIDDEN_COLS = ["idArticle", "idProduct"]
COLORED_COLS = {
    "Price": "FFF0F8FF",
    "SuggestedPrice": "949494E8"
}


def get_excel_col_name(df: pd.DataFrame, col_name: str) -> str:
    """Returns the letter to access the excel position of a column"""
    return string.ascii_uppercase[list(df.columns).index(col_name)]


def get_stock_file_path(folder_path: Path) -> Path:
    """Constructs the stock file path from a folder path"""
    return folder_path / "stock.xlsx"


def convert_base64_gzipped_string_to_dataframe(b64_zipped_string: str) -> pd.DataFrame:
    """Converts a base64 gzipped strings (or bytes) into a pandas dataframe"""
    decoded_string = base64.b64decode(b64_zipped_string)
    csv_string = gzip.decompress(decoded_string)

    return pd.read_csv(io.BytesIO(csv_string), sep=";")


def save_stock_df_as_odf_formatted_file(df: pd.DataFrame, file_path: Path) -> None:
    writer = pd.ExcelWriter(path=str(file_path))
    df.to_excel(excel_writer=writer, index=False)

    worksheet = writer.sheets['Sheet1']

    for col_name in ["idArticle", "idProduct"]:
        excel_col_name = get_excel_col_name(df=df, col_name=col_name)
        worksheet.column_dimensions[excel_col_name].hidden = True

    for col_name, color in COLORED_COLS.items():
        excel_col_name = get_excel_col_name(df=df, col_name=col_name)
        fill = PatternFill(start_color=color, end_color=color, fill_type='solid')

        worksheet.column_dimensions[excel_col_name].fill = fill

    writer.save()


def prepare_stock_df(stock_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the columns 'PriceApproval', 'Comments', 'RelativePriceDiff' and sorts the stock_df """
    stock_df["PriceApproval"] = 1
    stock_df["Comments"] = stock_df["Comments"].fillna("")

    no_suggested_price_or_already_manual_mask = pd.isna(
        obj=stock_df["SuggestedPrice"]
    ) & (~stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER))
    stock_df.loc[
        no_suggested_price_or_already_manual_mask, "Comments"
    ] += MANUAL_PRICE_MARKER
    stock_df.loc[
        stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER), "PriceApproval"
    ] = 0

    stock_df["RelativePriceDiff"] = (
        stock_df["Price"] - stock_df["SuggestedPrice"]
    ) / stock_df["SuggestedPrice"]

    return stock_df.sort_values(
        by=["PriceApproval", "RelativePriceDiff"], ascending=[True, False]
    )


def get_basic_stats(stock_df: pd.DataFrame) -> BasicStats:
    """Computes a few basic stats on the stock_df"""
    total_current_price = (stock_df["Price"] * stock_df["Amount"]).sum()

    non_set_prices = pd.isna(stock_df["SuggestedPrice"])
    stock_df.loc[non_set_prices, "SuggestedPrice"] = stock_df.loc[
        non_set_prices, "Price"
    ]
    total_suggested_price = (stock_df["SuggestedPrice"] * stock_df["Amount"]).sum()

    relative_diff = (
        (total_current_price - total_suggested_price) / total_current_price * 100
    )

    return BasicStats(
        total_current_price=total_current_price,
        total_suggested_price=total_suggested_price,
        relative_diff=relative_diff,
    )


MANUAL_PRICE_MARKER = "<manualPrice>"
