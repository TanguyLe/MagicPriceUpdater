import logging
from functools import partial
import os
import sys
from pathlib import Path

from pandarallel import pandarallel

from mpu.card_market_client import CardMarketClient
from mpu.log_conf import set_log_conf
from mpu.market_extract import set_market_extract_path, reset_market_extract, get_single_product_market_extract

# Extensions
sys.path.append(str(Path(__file__).parent / "MPUStrategies"))
from mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu_strategies.errors import SuitableExamplesShortage
from mpu_strategies.price_update import PriceUpdater

MANUAL_PRICE_MARKER = "<manualPrice>"


def main(
        current_price_strategy: str,
        price_update_strategy: str,
        market_extract_path: Path,
        output_path: Path,
        force_update: bool
):
    set_log_conf(log_path=os.getcwd())
    pandarallel.initialize(progress_bar=False)
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
        try:
            market_extract = _get_product_market_extract(product_id=product_id)
        except Exception as error:
            logger.error(f"Error when trying to extract data for product {product_id}: {error.__repr__()}")
            return float("nan")

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
        stock_df["SuggestedPrice"] = stock_df["idProduct"].parallel_apply(get_product_price)
    except Exception as error:
        logger.error(error)
        raise
    finally:
        stock_df.to_csv(output_path / "stock.csv")

    # df preparation
    stock_df["PriceApproval"] = 1
    stock_df["Comments"] = stock_df["Comments"].fillna('')
    stock_df.loc[stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER), "PriceApproval"] = 0
    stock_df["RelativePriceDiff"] = (stock_df["Price"] - stock_df["SuggestedPrice"]) / stock_df["SuggestedPrice"]

    stock_df = stock_df.sort_values(by=["PriceApproval", "RelativePriceDiff"], ascending=[True, False])

    # Adding or updating new prices columns
    stock_df = price_updater.get_updated_df(stock_df=stock_df)

    # Saves the result
    stock_df.to_csv(output_path / "stock.csv")

    logger.info("End of the run")
