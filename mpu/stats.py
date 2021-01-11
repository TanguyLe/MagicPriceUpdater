import logging
from pathlib import Path

import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.pyopenxl_utils import format_and_save_df, EXCEL_ENGINE

INDEX_NAME = "datetime"

COLUMNS_FORMAT = {
    INDEX_NAME: {"width": 10},
    "NbCards": {"width": 2.2},
    "NbFoil": {"width": 2.65},
    "NbNotFoil": {"width": 3},
    "FoilPercentage": {"width": 4},
    "NbCardsSup5": {"width": 3.5},
    "NbCardsInf0.30": {"width": 4},
    "AvgCardPrice": {"width": 4.25},
    "StockTotalValue": {"width": 4.25},
}
STATS_COLUMNS = [
    col_name for col_name in list(COLUMNS_FORMAT.keys()) if col_name != INDEX_NAME
]


def get_stats_file_path(folder_path: Path) -> Path:
    """Constructs the stats file path from a folder path"""
    return folder_path / "stockStats.xlsx"


def main(stats_file_path: Path):
    logger = logging.getLogger(__name__)
    logger.info("Starting stats...")

    client = CardMarketClient()
    stock_df = client.get_stock_df()

    logger.info("Loading the existing stats...")
    try:
        former_stats_df = pd.read_excel(io=stats_file_path, engine=EXCEL_ENGINE)
        former_stats_df[INDEX_NAME] = pd.to_datetime(former_stats_df[INDEX_NAME])
        former_stats_df = former_stats_df.set_index(INDEX_NAME)
    except FileNotFoundError:
        logger.info("Stats file not found, this run will create a new one.")
        former_stats_df = pd.DataFrame(columns=STATS_COLUMNS, index=pd.to_datetime([]))
        former_stats_df.index.name = INDEX_NAME
    else:
        if list(former_stats_df.columns) != STATS_COLUMNS or not isinstance(
            former_stats_df.index, pd.DatetimeIndex
        ):
            msg = f"The current stats df at {stats_file_path} is wrongly formatted, move it or delete it."
            logger.error(msg)
            raise RuntimeError(msg)

    logger.info("Stats loaded.")

    logger.info("Computing the stats...")

    stats_df = pd.DataFrame(index=pd.to_datetime([pd.Timestamp("now")]))
    stats_df.index.name = INDEX_NAME

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

    final_stats_df = pd.concat(
        objs=[former_stats_df.replace('', float("nan")).dropna(how="all"), stats_df.round(2)],
        axis="rows"
    )

    logger.info("Stats computing ended.")

    logger.info("Saving the stats...")

    writer = pd.ExcelWriter(path=str(stats_file_path), engine=EXCEL_ENGINE)
    final_stats_df.to_excel(excel_writer=writer, engine=EXCEL_ENGINE)
    format_and_save_df(
        df=final_stats_df.reset_index(), writer=writer, format_config=COLUMNS_FORMAT
    )

    logger.info(f"Stats saved at {stats_file_path}.")

    logger.info("stats complete.")
