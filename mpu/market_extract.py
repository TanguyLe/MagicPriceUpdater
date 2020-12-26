import json
import logging
import os
from functools import partial
from pathlib import Path

from mpu.card_market_client import CardMarketClient

logger = logging.getLogger(__name__)


def get_market_extract_path(market_extract_parent_path: Path):
    _market_extract_path = market_extract_parent_path / "market_extract"
    try:
        os.mkdir(_market_extract_path)
    except FileExistsError:
        pass

    return _market_extract_path


def get_market_extract_from_card_market(
    product_id: int,
    card_market_client: CardMarketClient,
    market_extract_path: Path,
    max_results: int = 100,
):
    product_market_extract = {
        "articles": card_market_client.get_product_articles(
            product_id=product_id, min_condition="EX", max_results=max_results
        ),
        "info": card_market_client.get_product_info(product_id=product_id),
    }

    logger.info(f"Saving market extract for {product_id}.")
    with (market_extract_path / f"{product_id}.json").open("w") as product_file:
        json.dump(obj=product_market_extract, fp=product_file)

    return product_market_extract


def get_single_product_market_extract(
    product_id: int,
    market_extract_path: Path,
    card_market_client: CardMarketClient,
    max_results: int = 100,
    force_update: bool = False,
) -> dict:
    """Get a product price from the local file if possible, otherwise from the API"""
    single_product_market_extract_path = market_extract_path / f"{product_id}.json"
    _get_market_extract_from_card_market = partial(
        get_market_extract_from_card_market,
        product_id=product_id,
        market_extract_path=market_extract_path,
        card_market_client=card_market_client,
        max_results=max_results,
    )

    if force_update:
        return _get_market_extract_from_card_market()

    try:
        with single_product_market_extract_path.open("r") as product_prices_file:
            return json.load(fp=product_prices_file)
    except FileNotFoundError:
        return _get_market_extract_from_card_market()
