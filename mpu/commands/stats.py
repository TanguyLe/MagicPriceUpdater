import logging
from pathlib import Path

import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.excel_formats import SHORT_STATS_COLUMNS_FORMAT, LARGE_STATS_COLUMNS_FORMAT, INDEX_NAME
from mpu.stats_calculations import aggregate_data
from mpu.stock_handling import prep_stock_df_for_stats
from mpu.utils.pyopenxl_utils import format_and_save_df, EXCEL_ENGINE

SHORT_STATS_SHEET_NAME = "Sheet1"
LARGE_STATS_SHEET_NAME = "large_stats"
GLOBAL = "Global"

SHORT_STATS_COLUMNS = {
    "NbCards": (GLOBAL, GLOBAL, "TNb"),
    "NbFoil": ("Foil?", "Y", "TNb"),
    "NbNotFoil": ("Foil?", "N", "TNb"),
    "FoilPercentage": ("Foil?", "Y", "%(Nb)"),
    "NbCardsSup5": ("Foil?", "Y", "%(Nb)"),
    "NbCardsInf0.30": ("PriceCategories", "Inf0.30", "TNb"),
    "AvgCardPrice": (GLOBAL, GLOBAL, "AvgVal"),
    "StockTotalValue": (GLOBAL, GLOBAL, "TVal")
}
STATS_COLUMNS = [
    col_name for col_name in list(SHORT_STATS_COLUMNS.keys()) if col_name != INDEX_NAME
]


def get_stats_file_path(folder_path: Path) -> Path:
    """Constructs the stats file path from a folder path"""
    return folder_path / "stockStats.xlsx"


def create_short_stats_df(current_timestamp: pd.DatetimeIndex, large_stats_df: pd.DataFrame) -> pd.DataFrame:
    short_stats_df = pd.DataFrame(index=current_timestamp)
    short_stats_df.index.name = INDEX_NAME

    for col_name, col_loc in SHORT_STATS_COLUMNS.items():
        short_stats_df[col_name] = large_stats_df[col_loc]

    short_stats_df["NbCardsSup5"] = (
            large_stats_df[("PriceCategories", "5to30", "TNb")]
            + large_stats_df[("PriceCategories", "Sup30", "TNb")]
    )

    return short_stats_df


def main(stats_file_path: Path):
    logger = logging.getLogger(__name__)
    logger.info("Starting stats...")

    client = CardMarketClient()
    stock_df = client.get_stock_df()

    logger.info("Loading the existing stats...")
    try:
        former_large_stats_df = pd.read_excel(
            io=stats_file_path, engine=EXCEL_ENGINE, sheet_name=LARGE_STATS_SHEET_NAME, header=[0, 1, 2], index_col=0
        )
        former_short_stats_df = pd.read_excel(
            io=stats_file_path, engine=EXCEL_ENGINE, sheet_name=SHORT_STATS_SHEET_NAME, index_col=0
        )
    except FileNotFoundError:
        logger.info("Stats file not found, this run will create a new one.")
        new_dfs = True
    else:
        new_dfs = False
        if list(former_short_stats_df.columns) != STATS_COLUMNS or not isinstance(
                former_short_stats_df.index, pd.DatetimeIndex
        ):
            msg = f"The current stats df at {stats_file_path} is wrongly formatted, move it or delete it."
            logger.error(msg)
            raise RuntimeError(msg)

    logger.info("Stats loaded.")
    logger.info("Computing the stats...")

    current_timestamp = pd.to_datetime([pd.Timestamp("now")])
    current_timestamp.name = INDEX_NAME

    stock_df = prep_stock_df_for_stats(stock_df=stock_df)

    large_stats_df = aggregate_data(data=stock_df, index=current_timestamp, index_name=GLOBAL)
    for group_col in ["PriceCategories", "Foil?", "Signed?", "Condition", "Language"]:
        large_stats_df = pd.concat(
            [
                large_stats_df,
                aggregate_data(data=stock_df, group_name=group_col, index=current_timestamp, index_name=group_col)
            ],
            axis="columns"
        )

    short_stats_df = create_short_stats_df(current_timestamp=current_timestamp, large_stats_df=large_stats_df)

    if not new_dfs:
        short_stats_df = pd.concat(
            objs=[former_short_stats_df.replace('', float("nan")).dropna(how="all"), short_stats_df],
            axis="rows"
        )
        large_stats_df = pd.concat(
            objs=[former_large_stats_df.replace('', float("nan")).dropna(how="all"), large_stats_df],
            axis="rows"
        )

    logger.info("Stats computing ended.")

    logger.info("Saving the stats...")

    writer = pd.ExcelWriter(path=str(stats_file_path), engine=EXCEL_ENGINE)
    short_stats_df.round(2).to_excel(excel_writer=writer, engine=EXCEL_ENGINE, sheet_name=SHORT_STATS_SHEET_NAME)
    large_stats_df.round(2).to_excel(excel_writer=writer, engine=EXCEL_ENGINE, sheet_name=LARGE_STATS_SHEET_NAME)
    format_and_save_df(
        df=short_stats_df.reset_index(), writer=writer, format_config=SHORT_STATS_COLUMNS_FORMAT,
        sheet_name=SHORT_STATS_SHEET_NAME
    )
    format_and_save_df(
        df=large_stats_df.reset_index(), writer=writer, format_config=LARGE_STATS_COLUMNS_FORMAT,
        sheet_name=LARGE_STATS_SHEET_NAME
    )

    logger.info(f"Stats saved at {stats_file_path}.")

    logger.info("stats complete.")
