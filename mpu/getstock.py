import logging
from functools import partial
import os
from pathlib import Path

import pandas as pd
from pandarallel import pandarallel

from mpu.card_market_client import CardMarketClient
from mpu.log_conf import set_log_conf
from mpu.market_extract import set_market_extract_path, reset_market_extract, get_single_product_market_extract

from mpu.MPUStrategies.mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu.MPUStrategies.mpu_strategies.errors import SuitableExamplesShortage
from mpu.MPUStrategies.mpu_strategies.price_update import PriceUpdater


def main(
        current_price_strategy: str,
        price_update_strategy: str,
        market_extract_path: Path,
        output_path: Path,
        force_update: bool
):
    set_log_conf(log_path=os.getcwd())
    pandarallel.initialize(progress_bar=True)
    logger = logging.getLogger(__name__)
    logger.info("Starting run")

    client = CardMarketClient()
    current_price_computer = CurrentPriceComputer(strategy_name=current_price_strategy)
    price_updater = PriceUpdater(strategy_name=price_update_strategy)

    # Get the stock as a dataframe
    stock_df = client.get_stock_df()

    # Set the market extract path
    set_market_extract_path(market_extract_parent_path=market_extract_path)

    # Load the saved product prices
    reset_market_extract(force_update=force_update)

    _get_product_market_extract = partial(get_single_product_market_extract, card_market_client=client)

    def get_product_price(product_id):
        market_extract = _get_product_market_extract(product_id=product_id)
        try:
            return current_price_computer.get_current_price_from_market_extract(market_extract=market_extract)
        except SuitableExamplesShortage:
            # We try with a larger request in case of a lack of suitable examples
            market_extract = _get_product_market_extract(product_id=product_id, max_results=500)
            try:
                return current_price_computer.get_current_price_from_market_extract(market_extract=market_extract)
            except SuitableExamplesShortage:
                return float("nan")

    # Put the product prices in the df
    try:
        stock_df["ActualPrice"] = stock_df["idProduct"].parallel_apply(get_product_price)
    except Exception as error:
        logger.error(error)
        raise
    finally:
        stock_df.to_csv(output_path / "stock.csv")

    # Computes the new price
    stock_df = price_updater.update_df_with_new_prices(stock_df=stock_df)

    # Saves the result
    stock_df.to_csv(output_path / "stock.csv")
    # Saves only the updated prices separately
    stock_df.loc[~pd.isna(stock_df["NewPrice"])].to_csv(output_path / "updated_stock.csv")

    logger.info("End of the run")
