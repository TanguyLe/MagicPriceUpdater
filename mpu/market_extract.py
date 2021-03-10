import json
import logging
import os
from functools import partial
from pathlib import Path

from mpu.card_market_client import CardMarketClient, get_language_id, get_conditions

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

    # TODO Refacto
    # TODO Do the request split also for this one
    return {
        **market_extract,
        **{"articles_foil": card_market_client.get_product_articles(
            product_id=stock_info["idProduct"],
            min_condition="EX",
            max_results=max_results,
            foil=True
        )}
    }


def get_product_articles_from_card_market_with_languages(
        stock_info: dict,
        card_market_client: CardMarketClient,
        config: dict,
        min_condition: str
):
    product_id = stock_info["idProduct"]

    languages_names = config.get("languages")
    if languages_names is None:
        return card_market_client.get_product_articles(
            product_id=product_id,
            min_condition=min_condition,
            max_results=config.get("default_max_results"),
        )

    # Case of multiple requests per language
    articles = []

    language_ids = [
        get_language_id(language) if language != "CARD" else stock_info["Language"] for language in languages_names
    ]
    # Removing duplicated languages
    language_ids = list(set(language_ids))

    for language_name, language_id in zip(languages_names, language_ids):
        max_results = config.get("max_results").get(language_name, config.get("default_max_results"))
        articles.extend(
            card_market_client.get_product_articles(
                product_id=product_id,
                min_condition=min_condition,
                max_results=max_results,
                language_id=language_id
            )
        )

    return articles


def get_product_articles_language_and_conditions(
        stock_info: dict, card_market_client: CardMarketClient, config: dict
):
    if not config.get("one_request_per_condition", False):
        return get_product_articles_from_card_market_with_languages(
            stock_info=stock_info,
            card_market_client=card_market_client,
            config=config,
            min_condition=config["min_condition"]
        )

    # Case of multiple requests per condition
    product_articles = []

    for condition in get_conditions(config["min_condition"]):
        product_articles.extend(
            get_product_articles_from_card_market_with_languages(
                stock_info=stock_info,
                card_market_client=card_market_client,
                config=config,
                min_condition=condition
            )
        )

    return product_articles


def get_market_extract_from_card_market(
        stock_info: dict,
        card_market_client: CardMarketClient,
        market_extract_path: Path,
        config: dict
):
    product_id = stock_info["idProduct"]

    product_market_extract = {
        "articles": get_product_articles_language_and_conditions(
            stock_info=stock_info,
            card_market_client=card_market_client,
            config=config
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
        config: dict,
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
        config=config
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
