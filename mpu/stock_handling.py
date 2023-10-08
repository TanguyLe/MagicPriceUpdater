from typing import NamedTuple

import pandas as pd

from mpu.card_market_client import LANGUAGES


class BasicStats(NamedTuple):
    total_current_price: float
    total_suggested_price: float
    relative_diff: float


MANUAL_PRICE_MARKER = "<M>"


def prepare_stock_df(_stock_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the columns 'PriceApproval', 'Comments', 'RelativePriceDiff' and sorts the stock_df"""
    _stock_df = _stock_df.copy()
    _stock_df["PriceApproval"] = 1
    _stock_df["Comments"] = _stock_df["Comments"].fillna("")

    no_suggested_price_or_already_manual_mask = pd.isna(
        obj=_stock_df["SuggestedPrice"]
    ) & (~_stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER))

    _stock_df.loc[no_suggested_price_or_already_manual_mask, "PriceApproval"] = 0

    _stock_df["RelativePriceDiff"] = (
        (_stock_df["SuggestedPrice"] - _stock_df["Price"]) / _stock_df["Price"] * 100
    )

    _stock_df["AbsRelativePriceDiff"] = _stock_df["RelativePriceDiff"].abs()
    _stock_df = _stock_df.sort_values(
        by=["PriceApproval", "AbsRelativePriceDiff"], ascending=[True, False]
    ).drop("AbsRelativePriceDiff", axis="columns")

    _stock_df["RelativePriceDiff"] = _stock_df["RelativePriceDiff"].round(2)

    _stock_df.insert(
        loc=list(_stock_df.columns).index("SuggestedPrice"),
        column="ManualPrice",
        value="",
    )

    return _stock_df


def get_basic_stats(stock_df: pd.DataFrame) -> BasicStats:
    """Computes a few basic stats on the stock_df"""
    total_current_price = (stock_df["Price"] * stock_df["Amount"]).sum()

    non_set_prices = pd.isna(stock_df["SuggestedPrice"])
    stock_df.loc[non_set_prices, "SuggestedPrice"] = stock_df.loc[
        non_set_prices, "Price"
    ]
    total_suggested_price = (stock_df["SuggestedPrice"] * stock_df["Amount"]).sum()

    relative_diff = (
        (total_suggested_price - total_current_price) / total_current_price * 100
    )

    return BasicStats(
        total_current_price=total_current_price,
        total_suggested_price=total_suggested_price,
        relative_diff=relative_diff,
    )


def prep_stock_df_for_stats(stock_df: pd.DataFrame) -> pd.DataFrame:
    # Stock df prep
    stock_df["PriceCategories"] = pd.cut(
        x=stock_df["Price"],
        bins=[0, 0.3, 2, 10, 20, 30, 1000000],
        labels=["Inf0.30", "0.30to2", "2to10", "10to20", "20to30", "Sup30"],
        include_lowest=True,
        right=False,
    )
    stock_df["Foil?"] = (
        stock_df["Foil?"].replace({"X": "Y", "1.0": "Y", 1.0: "Y"}).fillna("N")
    )
    stock_df["Signed?"] = (
        stock_df["Signed?"].replace({"X": "Y", "1.0": "Y", 1.0: "Y"}).fillna("N")
    )
    stock_df["PriceXAmount"] = stock_df["Price"] * stock_df["Amount"]
    stock_df["Language"] = stock_df["Language"].replace(
        {(index + 1): name for index, name in enumerate(LANGUAGES)}
    )
    stock_df.loc[
        ~stock_df["Language"].isin(["English", "French"]), "Language"
    ] = "Other"

    return stock_df
