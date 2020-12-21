import logging
from pathlib import Path

import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.log_utils import DATE_FMT


def main(output_path: Path):
    logger = logging.getLogger(__name__)
    logger.info("Starting stats...")

    stats_output_path = (
        output_path / f"stockStats-{pd.Timestamp('now').strftime(DATE_FMT)}.xlsx"
    )

    client = CardMarketClient()
    stock_df = client.get_stock_df()

    logger.info("Computing the stats...")

    stats_df = pd.DataFrame(index=["value"])

    foil_stats = (
        stock_df.replace(to_replace={"X": "Y"})
        .fillna("N")
        .groupby(by="Foil?")
        .agg({"Amount": "sum"})
    )
    stats_df["NbFoil"] = foil_stats.loc["Y", "Amount"]
    stats_df["NbNotFoil"] = foil_stats.loc["N", "Amount"]
    stats_df["FoilPercentage"] = (foil_stats.loc["Y"] / foil_stats.sum() * 100)[0]

    stats_df["NbCards"] = stock_df["Amount"].sum()
    stats_df["AvgCardPrice"] = stock_df["Price"].mean()
    stats_df["StockTotalValue"] = (stock_df["Amount"] * stock_df["Price"]).sum()
    stats_df["NbCardsSup5"] = ((stock_df["Price"] > 5) * stock_df["Amount"]).sum()
    stats_df["NbCardsInf0.30"] = ((stock_df["Price"] < 0.30) * stock_df["Amount"]).sum()

    stats_df = stats_df.T.reset_index()
    stats_df.columns = ["stat", "value"]
    stats_df = stats_df.set_index("stat")

    logger.info("Stats computing ended.")

    logger.info("Saving the stats...")
    stats_df.to_excel(excel_writer=str(stats_output_path))
    logger.info(f"Stats saved at {stats_output_path}.")

    logger.info("stats complete.")
