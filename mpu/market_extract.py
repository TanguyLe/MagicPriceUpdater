import json
import logging
import os
from functools import partial
from pathlib import Path

from mpu.card_market_client import CardMarketClient

logger = logging.getLogger(__name__)


def get_market_extract_path(market_extract_parent_path: Path) -> Path:
    _market_extract_path = market_extract_parent_path / "market_extract"
    try:
        os.mkdir(str(_market_extract_path))
    except FileExistsError:
        pass

    return _market_extract_path


def save_market_extract(product_market_extract: dict, market_extract_path: Path, product_id: int) -> None:
    logger.info(f"Saving market extract for {product_id}.")
    with (market_extract_path / f"{product_id}.json").open("w") as product_file:
        json.dump(obj=product_market_extract, fp=product_file)


def add_foil_articles_if_needed(
        market_extract: dict,
        stock_info: dict,
        card_market_client: CardMarketClient,
        max_results: int = 50
):
    if market_extract.get("articles_foil") is not None or stock_info["Foil?"] == '':
        return market_extract

    return {
        **market_extract,
        **{"articles_foil": card_market_client.get_product_articles(
                                product_id=stock_info["idProduct"],
                                min_condition="EX",
                                max_results=max_results,
                                foil=True
        )}
    }


def get_market_extract_from_card_market(
    stock_info: dict,
    card_market_client: CardMarketClient,
    market_extract_path: Path,
    max_results: int = 100,
):
    product_id = stock_info["idProduct"]

    product_market_extract = {
        "articles": card_market_client.get_product_articles(
            product_id=product_id,
            min_condition="EX",
            max_results=max_results
        ),
        "info": card_market_client.get_product_info(product_id=product_id),
    }
    add_foil_articles_if_needed(
        card_market_client=card_market_client,
        stock_info=stock_info,
        market_extract=product_market_extract,
        max_results=50
    )

    save_market_extract(
        product_market_extract=product_market_extract,
        product_id=product_id,
        market_extract_path=market_extract_path
    )

    return product_market_extract


def get_single_product_market_extract(
    stock_info: dict,
    market_extract_path: Path,
    card_market_client: CardMarketClient,
    max_results: int = 100,
    force_update: bool = False,
) -> dict:
    """Get a product price from the local file if possible, otherwise from the API"""
    product_id = stock_info["idProduct"]

    single_product_market_extract_path = market_extract_path / f"{product_id}.json"
    _get_market_extract_from_card_market = partial(
        get_market_extract_from_card_market,
        stock_info=stock_info,
        market_extract_path=market_extract_path,
        card_market_client=card_market_client,
        max_results=max_results,
    )

    if force_update:
        return _get_market_extract_from_card_market()

    try:
        with single_product_market_extract_path.open("r") as product_prices_file:
            product_market_extract = json.load(fp=product_prices_file)
            new_product_market_extract = add_foil_articles_if_needed(
                card_market_client=card_market_client,
                stock_info=stock_info,
                market_extract=product_market_extract,
                max_results=50
            )
            if new_product_market_extract != product_market_extract:
                save_market_extract(
                    product_market_extract=new_product_market_extract,
                    product_id=product_id,
                    market_extract_path=market_extract_path
                )

            return product_market_extract

    except FileNotFoundError:
        return _get_market_extract_from_card_market()
