import logging
import json
import os

from mpu.card_market_client import CardMarketClient

logger = logging.getLogger(__name__)

_market_extract = {}
_market_extract_path = None


def set_market_extract_path(market_extract_parent_path):
    global _market_extract_path
    _market_extract_path = market_extract_parent_path / "market_extract"
    try:
        os.mkdir(_market_extract_path)
    except FileExistsError:
        pass


def raise_if_market_extract_path_not_set(function):
    def wrapped_func(*args, **kwargs):
        if _market_extract_path is None:
            raise RuntimeError("Call set_market_extract_path before running any market_path option!")
        return function(*args, **kwargs)
    return wrapped_func


def get_market_extract():
    """Returns the current product prices"""
    return _market_extract


@raise_if_market_extract_path_not_set
def reset_market_extract(force_update=False):
    """Resets the current product prices, either to the state of the file or a force update to empty prices"""
    global _market_extract

    if force_update:
        _market_extract = {}

    for file in _market_extract_path.iterdir():
        if ".json" in file.name:
            with (_market_extract_path / file).open('r') as product_prices_file:
                _market_extract[file.name.rstrip(".json")] = json.load(fp=product_prices_file)


@raise_if_market_extract_path_not_set
def save_single_product_market_extract(product_id: str):
    try:
        product_data = get_market_extract()[product_id]
    except KeyError:
        raise ValueError(f"Market extract does not exist for product {product_id}.")

    logger.info(f"Saving market extract for {product_id}.")
    with (_market_extract_path / f"{product_id}.json").open('w') as product_file:
        json.dump(obj=product_data, fp=product_file)


@raise_if_market_extract_path_not_set
def get_single_product_market_extract(product_id: int, card_market_client: CardMarketClient, max_results=100) -> dict:
    """Get a product price from the local file if possible, otherwise from the API"""
    market_extract = get_market_extract()
    product_id_str = str(product_id)

    try:
        return market_extract[product_id_str]
    except KeyError:
        product_data = {
            "articles": card_market_client.get_product_articles(
                product_id=product_id, min_condition="EX", max_results=max_results
            ),
            "info": card_market_client.get_product_info(product_id=product_id)
        }
        market_extract[product_id_str] = product_data

        save_single_product_market_extract(product_id=product_id_str)

        return product_data
