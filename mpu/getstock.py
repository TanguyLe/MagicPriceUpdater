import logging
from functools import partial
import os
import sys
from pathlib import Path

from pandarallel import pandarallel
import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.log_conf import set_log_conf
from mpu.market_extract import set_market_extract_path, get_single_product_market_extract

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
        force_update: bool,
        parallel_execution: bool
):
    set_log_conf(log_path=os.getcwd())
    if parallel_execution:
        pandarallel.initialize(progress_bar=False)
    logger = logging.getLogger(__name__)
    logger.info("Starting run")

    client = CardMarketClient()
    current_price_computer = CurrentPriceComputer(strategy_name=current_price_strategy)
    price_updater = PriceUpdater(strategy_name=price_update_strategy)

    stock_output_path = output_path / "stock.csv"

    logger.info("Getting the stock from Card Market...")
    # Get the stock as a dataframe
    stock_df = client.get_stock_df()
    logger.info("Stock retrieved.")

    # Set the market extract path
    set_market_extract_path(market_extract_parent_path=market_extract_path)

    _get_product_market_extract = partial(
        get_single_product_market_extract,
        card_market_client=client,
        force_update=force_update
    )

    def get_product_price(row):
        stock_info = row.to_dict()
        product_id = stock_info["idProduct"]
        try:
            market_extract = _get_product_market_extract(product_id=product_id)
        except Exception as error:
            logger.error(f"Error when trying to extract data for product {product_id}: {error.__repr__()}")
            return float("nan")

        try:
            return current_price_computer.get_current_price_from_market_extract(
                stock_info=stock_info, market_extract=market_extract
            )
        except SuitableExamplesShortage:
            # We try with a larger request in case of a lack of suitable examples
            market_extract = _get_product_market_extract(product_id=product_id, max_results=500)
            try:
                return current_price_computer.get_current_price_from_market_extract(
                    stock_info=stock_info, market_extract=market_extract
                )
            except SuitableExamplesShortage:
                return float("nan")

    logger.info("Computing the new prices...")
    # Put the product prices in the df
    try:
        if parallel_execution:
            product_price = stock_df.parallel_apply(get_product_price, axis="columns")
        else:
            product_price = stock_df.apply(get_product_price, axis="columns")
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
    # df preparation
    stock_df["PriceApproval"] = 1
    stock_df["Comments"] = stock_df["Comments"].fillna('')
    stock_df.loc[stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER), "PriceApproval"] = 0
    stock_df["RelativePriceDiff"] = (stock_df["Price"] - stock_df["SuggestedPrice"]) / stock_df["SuggestedPrice"]

    stock_df = stock_df.sort_values(by=["PriceApproval", "RelativePriceDiff"], ascending=[True, False])

    # Adding or updating new prices columns
    stock_df = price_updater.get_updated_df(stock_df=stock_df)
    logger.info("New columns computing ended.")

    # Saves the result
    logger.info("Saving the stock...")
    stock_df.to_csv(stock_output_path)
    logger.info(f"Stock saved at {stock_output_path}.")

    # A few stats already
    total_current_price = (stock_df["Price"] * stock_df["Amount"]).sum()

    non_set_prices = pd.isna(stock_df["SuggestedPrice"])
    stock_df.loc[non_set_prices, "SuggestedPrice"] = stock_df.loc[non_set_prices, "Price"]
    total_suggested_price = (stock_df["SuggestedPrice"] * stock_df["Amount"]).sum()

    relative_diff = (total_current_price - total_suggested_price) / total_current_price * 100

    logger.info(f"Worth: current:{total_current_price} / suggested:{total_suggested_price} / diff:{relative_diff:.2f}%")

    logger.info("End of the run.")
