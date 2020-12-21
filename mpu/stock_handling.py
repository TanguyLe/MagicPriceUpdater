from typing import NamedTuple

import pandas as pd


class BasicStats(NamedTuple):
    total_current_price: float
    total_suggested_price: float
    relative_diff: float


MANUAL_PRICE_MARKER = "<M>"


def prepare_stock_df(stock_df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the columns 'PriceApproval', 'Comments', 'RelativePriceDiff' and sorts the stock_df """
    stock_df["PriceApproval"] = 1
    stock_df["Comments"] = stock_df["Comments"].fillna("")

    no_suggested_price_or_already_manual_mask = pd.isna(
        obj=stock_df["SuggestedPrice"]
    ) & (~stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER))

    stock_df.loc[no_suggested_price_or_already_manual_mask, "PriceApproval"] = 0

    stock_df["RelativePriceDiff"] = (
        stock_df["SuggestedPrice"] - stock_df["Price"]
    ) / stock_df["Price"] * 100

    stock_df["AbsRelativePriceDiff"] = stock_df["RelativePriceDiff"].abs()
    stock_df = stock_df.sort_values(
        by=["PriceApproval", "AbsRelativePriceDiff"], ascending=[True, False]
    ).drop("AbsRelativePriceDiff", axis="columns")

    stock_df["RelativePriceDiff"] = stock_df["RelativePriceDiff"].round(2)

    return stock_df


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
