import logging
from functools import partial
import sys
from pathlib import Path

import pandas as pd
from pandarallel import pandarallel

from mpu.card_market_client import CardMarketClient
from mpu.constants import DATA_PATH
from mpu.log_conf import set_log_conf
from mpu.market_extract import reset_market_extract, get_single_product_market_extract

# To load the strategies
sys.path.append(Path(__file__).parent.parent / "MPUStrategies")
from mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu_strategies.errors import SuitableExamplesShortage
from mpu_strategies.price_update import PriceUpdater


STOCK_FILE_PATH = DATA_PATH / "stock.csv"
UPDATED_PRICES_STOCK_FILE_PATH = DATA_PATH / "updated_stock.csv"

# this should be a cli argument to the script later on
force_update = False

if __name__ == "__main__":
    set_log_conf()
    pandarallel.initialize(progress_bar=True)
    logger = logging.getLogger(__name__)
    logger.info("Starting run")

    client = CardMarketClient()
    current_price_computer = CurrentPriceComputer(strategy_name="naive")
    price_updater = PriceUpdater(strategy_name="initial")

    # Get the stock as a dataframe
    stock_df = client.get_stock_df()

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
        stock_df.to_csv(STOCK_FILE_PATH)

    # Computes the new price
    stock_df = price_updater.update_df_with_new_prices(stock_df=stock_df)

    # Saves the result
    stock_df.to_csv(STOCK_FILE_PATH)
    # Saves only the updated prices separately
    stock_df.loc[~pd.isna(stock_df["NewPrice"])].to_csv(UPDATED_PRICES_STOCK_FILE_PATH)

    logger.info("End of the run")
