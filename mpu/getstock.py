import logging
import os
from pathlib import Path
from typing import Optional

from pandarallel import pandarallel
import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.log_conf import set_log_conf
from mpu.market_extract import set_market_extract_path, get_single_product_market_extract
from mpu.stock_handling import prepare_stock_df, get_basic_stats
from mpu.strategies_utils import get_strategies_options

from mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu_strategies.errors import SuitableExamplesShortage
from mpu_strategies.price_update import PriceUpdater


def get_product_price(
        row: pd.Series,
        current_price_computer: CurrentPriceComputer,
        logger: logging.Logger,
        card_market_client: CardMarketClient,
        force_update: bool
) -> float:
    stock_info: dict = row.to_dict()
    product_id = stock_info["idProduct"]
    try:
        market_extract = get_single_product_market_extract(
            product_id=product_id, card_market_client=card_market_client, force_update=force_update
        )
    except Exception as error:
        logger.error(f"Error when trying to extract data for product {product_id}: {error.__repr__()}")
        return float("nan")

    try:
        return current_price_computer.get_current_price_from_market_extract(
            stock_info=stock_info, market_extract=market_extract
        )
    except SuitableExamplesShortage:
        # We try with a larger request in case of a lack of suitable examples
        market_extract = get_single_product_market_extract(
            product_id=product_id, card_market_client=card_market_client, force_update=force_update, max_results=500
        )
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
        parallel_execution: bool
):
    set_log_conf(log_path=os.getcwd())

    if parallel_execution:
        pandarallel.initialize(progress_bar=False)

    logger = logging.getLogger(__name__)
    logger.info("Starting run")

    stock_output_path = output_path / "stock.csv"
    strategies_options = get_strategies_options(strategies_options_path=strategies_options_path)
    set_market_extract_path(market_extract_parent_path=market_extract_path)

    logger.info(
        f"Using the following strategies: current_price={current_price_strategy} / price_update={price_update_strategy}"
    )
    logger.info(
        f"With the following options: {strategies_options}"
    )
    logger.info(
        f"Setting up the client and the strategies..."
    )
    client = CardMarketClient()
    current_price_computer = CurrentPriceComputer(
        strategy_name=current_price_strategy, **strategies_options.current_price
    )
    price_updater = PriceUpdater(
        strategy_name=price_update_strategy, **strategies_options.price_update
    )
    logger.info(
        f"Client and strategies initialized."
    )

    get_product_price_kwargs = {
        "axis": "columns",
        "current_price_computer": current_price_computer,
        "card_market_client": client,
        "logger": logger,
        "force_update": force_update
    }

    logger.info("Getting the stock from Card Market...")
    # Get the stock as a dataframe
    stock_df = client.get_stock_df()
    logger.info("Stock retrieved.")

    logger.info("Computing the new prices...")
    # Put the product prices in the df
    try:
        if parallel_execution:
            product_price = stock_df.parallel_apply(
                get_product_price,
                **get_product_price_kwargs
            )
        else:
            product_price = stock_df.apply(
                get_product_price,
                **get_product_price_kwargs
            )
    except Exception as error:
        logger.error("An error happened while computing prices.")
        logger.error(error)
        raise
    else:
        stock_df["SuggestedPrice"] = product_price
    finally:
        logger.info("Prices computing ended.")
        logger.info("Saving the stock before computing the new columns...")
        stock_df.to_csv(path_or_buf=stock_output_path)
        logger.info(f"Stock saved at {stock_output_path}.")

    logger.info("Computing the new columns...")
    stock_df = prepare_stock_df(stock_df=stock_df)
    logger.info("Using the price_update strategy...")
    stock_df = price_updater.get_updated_df(stock_df=stock_df)
    logger.info("New columns computing ended.")

    # Saves the result
    logger.info("Saving the stock...")
    stock_df.to_csv(stock_output_path)
    logger.info(f"Stock saved at {stock_output_path}.")

    # A few stats already
    basic_stats = get_basic_stats(stock_df=stock_df)

    logger.info(
        f"Worth: current:{basic_stats.total_current_price} "
        f"/ suggested:{basic_stats.total_suggested_price} "
        f"/ diff:{basic_stats.relative_diff:.2f}%"
    )

    logger.info("End of the run.")
