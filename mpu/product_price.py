import logging
from functools import partial
from pathlib import Path

import pandas as pd

from mpu.card_market_client import CardMarketClient
from mpu.market_extract import get_single_product_market_extract
from mpu.utils.strategies_utils import CurrentPriceComputer, SuitableExamplesShortage


def get_product_price(
        row: pd.Series,
        market_extract_path: Path,
        current_price_computer: CurrentPriceComputer,
        card_market_client: CardMarketClient,
        force_update: bool,
        config: dict
) -> float:
    logger = logging.getLogger(__name__)

    stock_info: dict = row.to_dict()
    product_id = stock_info["idProduct"]
    _get_single_product_market_extract = partial(
        get_single_product_market_extract,
        stock_info=stock_info,
        market_extract_path=market_extract_path,
        card_market_client=card_market_client,
        force_update=force_update,
        config=config
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
