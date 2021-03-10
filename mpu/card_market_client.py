import logging
from typing import Optional

import pandas as pd
from furl import furl

from mpu.oauth_client import OAuthAuthenticatedClient
from mpu.stock_io import convert_base64_gzipped_string_to_dataframe

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "French"
LANGUAGES = (
    "English", "French", "German", "Spanish", "Italian", "Simplified Chinese",
    "Japanese", "Portuguese", "Russian", "Korean", "Traditional Chinese"
)
CONDITIONS = ("MT", "NM", "EX", "GD", "LP", "PL", "PO")


def get_language_id(language: str):
    try:
        return LANGUAGES.index(language) + 1
    except ValueError:
        logger.error("Unknown language \"%s\", using \"%s\"", language, DEFAULT_LANGUAGE)
        return LANGUAGES.index(DEFAULT_LANGUAGE) + 1


class CardMarketClient(OAuthAuthenticatedClient):
    CARD_MARKET_API_URL = furl("https://api.cardmarket.com/ws/v2.0/output.json")

    def get_stock_df(self) -> pd.DataFrame:
        logger.info("Getting the stock from Card Market...")

        response = self.get_api_call(url=self.CARD_MARKET_API_URL / "stock/file")
        stock_string = response.json()["stock"]

        result = convert_base64_gzipped_string_to_dataframe(
            b64_zipped_string=stock_string
        )
        logger.info("Stock retrieved.")
        return result

    def get_product_info(self, product_id: int) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/products/{product_id}"
        response = self.get_api_call(url=call_url)

        return response.json()

    def get_product_articles(
        self,
        product_id: int,
        min_condition: Optional[str] = None,
        max_results: int = 100,
        language_id: Optional[int] = None,
        foil: Optional[bool] = None
    ) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/articles/{product_id}"
        if max_results is not None:
            call_url.add(args={"start": 0, "maxResults": max_results})
        if min_condition is not None:
            call_url.add(args={"minCondition": min_condition})
        if foil is not None:
            call_url.add(args={"isFoil": foil})
        if language_id is not None:
            call_url.add(args={"idLanguage": language_id})

        call_url.add(args={"isSigned": False, "isAltered": False})

        response = self.get_api_call(url=call_url)

        return response.json()["article"]

    def update_articles_prices(self, articles_data):
        call_url = self.CARD_MARKET_API_URL / "stock"
        response = self.put_api_call(data=articles_data, url=call_url)

        return response.json()
