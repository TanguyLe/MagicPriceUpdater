import logging
from functools import partial
from pathlib import Path
from typing import Optional
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.market_extract import get_single_product_market_extract, get_market_extract_path
from mpu.stock_handling import get_basic_stats, prepare_stock_df
from mpu.stock_io import get_stock_file_path, save_stock_df_as_odf_formatted_file
from mpu.strategies_utils import (
    CurrentPriceComputer,
    PriceUpdater,
    get_strategies_options,
    SuitableExamplesShortage
)


def get_product_price(
    row: pd.Series,
    market_extract_path: Path,
    current_price_computer: CurrentPriceComputer,
    card_market_client: CardMarketClient,
    force_update: bool,
) -> float:
    logger = logging.getLogger(__name__)

    stock_info: dict = row.to_dict()
    product_id = stock_info["idProduct"]
    _get_single_product_market_extract = partial(
        get_single_product_market_extract,
        product_id=product_id,
        market_extract_path=market_extract_path,
        card_market_client=card_market_client,
        force_update=force_update
    )

    try:
        market_extract = _get_single_product_market_extract()
    except Exception as error:
        logger.error(
            f"Error when trying to extract data for product {product_id}: {error.__repr__()}"
        )
        return float("nan")

    try:
        return current_price_computer.get_current_price_from_market_extract(
            stock_info=stock_info, market_extract=market_extract
        )
    except SuitableExamplesShortage:
        # We try with a larger request in case of a lack of suitable examples
        market_extract = _get_single_product_market_extract(max_results=500)
        try:
            return current_price_computer.get_current_price_from_market_extract(
                stock_info=stock_info, market_extract=market_extract
            )
        except SuitableExamplesShortage:
            return float("nan")


def main(
    current_price_strategy: str,
    price_update_strategy: str,
    strategies_options_path: Optional[Path],
    market_extract_path: Path,
    output_path: Path,
    force_update: bool,
    parallel_execution: bool,
):
    logger = logging.getLogger(__name__)
    logger.info("Starting getstock...")

    if parallel_execution:
        executor = ProcessPoolExecutor()
        logger.info(f"Parallel execution on {executor._max_workers} workers.")

    market_extract_path = get_market_extract_path(market_extract_parent_path=market_extract_path)
    logger.info(f"Market extract at {market_extract_path}.")

    stock_output_path = get_stock_file_path(folder_path=output_path)
    strategies_options = get_strategies_options(strategies_options_path=strategies_options_path)

    logger.info(
        f"Using the following strategies: current_price={current_price_strategy} / price_update={price_update_strategy}"
    )
    logger.info(f"With the following input options: {strategies_options}")
    logger.info(f"Setting up the client and the strategies...")
    client = CardMarketClient()
    current_price_computer = CurrentPriceComputer(
        strategy_name=current_price_strategy, **strategies_options.current_price
    )
    price_updater = PriceUpdater(
        strategy_name=price_update_strategy, **strategies_options.price_update
    )
    logger.info(f"Client and strategies initialized.")

    get_product_price_with_args = partial(
        get_product_price,
        current_price_computer=current_price_computer,
        market_extract_path=market_extract_path,
        card_market_client=client,
        force_update=force_update
    )

    stock_df = client.get_stock_df()
    logger.info("Computing the new prices...")
    # Put the product prices in the df
    try:
        if parallel_execution:
            rows = [row for _, row in stock_df.fillna('').iterrows()]
            product_price = list(executor.map(get_product_price_with_args, rows, chunksize=10))
            executor.shutdown()
        else:
            product_price = stock_df.apply(get_product_price_with_args)
    except Exception as error:
        logger.error("An error happened while computing prices.")
        logger.error(error)
        raise
    else:
        stock_df["SuggestedPrice"] = product_price
    finally:
        logger.info("Prices computing ended.")

    logger.info("Computing the new columns...")
    stock_df = prepare_stock_df(stock_df=stock_df)
    logger.info("Using the price_update strategy...")
    stock_df = price_updater.get_updated_df(stock_df=stock_df)
    logger.info("New columns computing ended.")

    # Saves the result
    logger.info("Saving the stock...")
    save_stock_df_as_odf_formatted_file(file_path=stock_output_path, df=stock_df)
    logger.info(f"Stock saved at {stock_output_path}.")

    # A few stats already
    basic_stats = get_basic_stats(stock_df=stock_df)

    logger.info(
        f"Worth: current:{basic_stats.total_current_price} "
        f"/ suggested:{basic_stats.total_suggested_price} "
        f"/ diff:{basic_stats.relative_diff:.2f}%"
    )

    logger.info("getstock complete.")
