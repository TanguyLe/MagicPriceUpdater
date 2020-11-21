import logging
import json

from mpu.card_market_client import CardMarketClient
from mpu.constants import DATA_PATH

MARKET_EXTRACT_FOLDER_PATH = DATA_PATH / "market_extract"

logger = logging.getLogger(__name__)

_market_extract = {}


def get_market_extract():
    """Returns the current product prices"""
    return _market_extract


def reset_market_extract(force_update=False):
    """Resets the current product prices, either to the state of the file or a force update to empty prices"""
    global _market_extract

    if force_update:
        _market_extract = {}

    for file in MARKET_EXTRACT_FOLDER_PATH.iterdir():
        if ".json" in file.name:
            with (MARKET_EXTRACT_FOLDER_PATH / file).open('r') as product_prices_file:
                _market_extract[file.name.rstrip(".json")] = json.load(fp=product_prices_file)


def save_single_product_market_extract(product_id: str):
    try:
        product_data = get_market_extract()[product_id]
    except KeyError:
        raise ValueError(f"Market extract does not exist for product {product_id}.")

    logger.info(f"Saving market extract for {product_id}.")
    with (MARKET_EXTRACT_FOLDER_PATH / f"{product_id}.json").open('w') as product_file:
        json.dump(obj=product_data, fp=product_file)


def get_single_product_market_extract(product_id: int, card_market_client: CardMarketClient) -> dict:
    """Get a product price from the local file if possible, otherwise from the API"""
    market_extract = get_market_extract()
    product_id_str = str(product_id)

    try:
        return market_extract[product_id_str]
    except KeyError:
        product_data = {
            "articles": card_market_client.get_product_articles(product_id=product_id, min_condition="EX"),
            "info": card_market_client.get_product_info(product_id=product_id)
        }
        market_extract[product_id_str] = product_data

        save_single_product_market_extract(product_id=product_id_str)

        return product_data
