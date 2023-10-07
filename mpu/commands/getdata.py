import logging
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

from mpu.card_market_client import CardMarketClient
from mpu.config_handling import load_config_file
from mpu.market_extract import (
    get_market_extract_path,
)
from mpu.utils.pyopenxl_utils import EXCEL_ENGINE
from mpu.product_price import get_single_product_market_extract
from mpu.stock_io import get_stock_file_path

import pandas as pd


def main(
    input_path: Path,
    config_path: Path,
    market_extract_path: Path,
    minimum_price: float,
    force_update: bool,
    parallel_execution: bool,
):
    logger = logging.getLogger(__name__)
    logger.info("Starting getstockdata...")

    stock_input_file_path = get_stock_file_path(folder_path=input_path, csv=True)

    if parallel_execution:
        executor = ProcessPoolExecutor()
        logger.info(f"Parallel execution on {executor._max_workers} workers.")

    market_extract_path = get_market_extract_path(
        market_extract_parent_path=market_extract_path
    )
    logger.info(f"Market extract at {market_extract_path}.")

    config = load_config_file(config_file_path=config_path)

    logger.info(f"Setting up the client...")
    client = CardMarketClient()
    logger.info(f"Client initialized.")

    get_single_product_market_extract_with_args = partial(
        get_single_product_market_extract,
        market_extract_path=market_extract_path,
        card_market_client=client,
        config=config["request_options"],
        force_update=force_update,
    )

    logger.info(f"Loading stock excel from {stock_input_file_path}...")
    stock_df = pd.read_csv(stock_input_file_path)
    stock_df = stock_df.fillna("")
    logger.info("Stock loaded.")

    if minimum_price:
        stock_df = stock_df[stock_df["Price"] >= minimum_price]
        logger.info(f"Removed articles whose price is under {minimum_price}.")

    stock_df_for_strategies = stock_df.fillna("")

    logger.info("Extracting market data...")
    try:
        if parallel_execution:
            rows = [row for _, row in stock_df_for_strategies.iterrows()]
            executor.map(get_single_product_market_extract_with_args, rows, chunksize=10)
            executor.shutdown()
        else:
            stock_df_for_strategies.apply(
                get_single_product_market_extract_with_args, axis="columns"
            )
    except Exception as error:
        logger.error("An error happened while extracting market data.")
        logger.error(error)
        raise
    finally:
        logger.info("Market data extraction ended.")

    logger.info("getstockdata complete.")
