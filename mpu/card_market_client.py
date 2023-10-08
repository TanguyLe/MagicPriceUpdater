import logging
from typing import Optional

import pandas as pd
from furl import furl
import requests

from mpu.utils.oauth_client import OAuthAuthenticatedClient
from mpu.stock_io import convert_base64_gzipped_string_to_dataframe

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "French"
LANGUAGES = (
    "English",
    "French",
    "German",
    "Spanish",
    "Italian",
    "Simplified Chinese",
    "Japanese",
    "Portuguese",
    "Russian",
    "Korean",
    "Traditional Chinese",
)
CONDITIONS = ("MT", "NM", "EX", "GD", "LP", "PL", "PO")


class CardMarketApiError(requests.HTTPError):
    """Error when requesting the API"""
    @classmethod
    def from_card_market_error(cls, error: requests.HTTPError) -> "CardMarketApiError":
        limit_count = error.response.headers.get("x-request-limit-count")
        limit_max = error.response.headers.get("x-request-limit-max")
        return cls(
            message=f"HTTP error on {error.request.url}: {error} - {error.response.content}",
            code=int(error.response.status_code),
            limit_count=int(limit_count) if limit_count is not None else None,
            limit_max=int(limit_max) if limit_max is not None else None
        )

    def __init__(self, message: str, code: int, limit_count: Optional[int], limit_max: Optional[int]) -> None:
        self.code = code
        self.limit_count = limit_count
        self.limit_max = limit_max

        super().__init__(message)

    @property
    def exceeded_request_limit(self):
        if self.limit_count is None or self.limit_max is None:
            return False

        return self.code == 429 and self.limit_count >= self.limit_max


def get_language_id(language: str):
    try:
        return LANGUAGES.index(language) + 1
    except ValueError:
        logger.error('Unknown language "%s", using "%s"', language, DEFAULT_LANGUAGE)
        return LANGUAGES.index(DEFAULT_LANGUAGE) + 1


def get_conditions(min_condition: str):
    try:
        lowest_quality_index = CONDITIONS.index(min_condition)
    except ValueError:
        raise ValueError(
            'Unknown condition "%s", use one of %s', min_condition, CONDITIONS
        )

    for condition in CONDITIONS[:lowest_quality_index]:
        yield condition


class CardMarketClient(OAuthAuthenticatedClient):
    CARD_MARKET_API_URL = furl("https://api.cardmarket.com/ws/v2.0/output.json")

    def get_stock_df(self) -> pd.DataFrame:
        logger.info("Getting the stock from Card Market...")

        response = self.get_api_call(url=self.CARD_MARKET_API_URL / "stock/file")
        stock_string = response.json()["stock"]

        limit_count = response.headers.get("x-request-limit-count")
        limit_max = response.headers.get("x-request-limit-max")
        logger.info(f"Limit: {limit_count}/{limit_max}.")

        result = convert_base64_gzipped_string_to_dataframe(
            b64_zipped_string=stock_string
        )
        logger.info("Stock retrieved.")
        return result

    def get_product_info(self, product_id: int) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/products/{product_id}"
        response = self.get_api_call(url=call_url)

        return response.json()

    def get_article_info(self, article_id: int) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/stock/article/{article_id}"
        response = self.get_api_call(url=call_url)

        return response.json()

    def get_product_articles(
        self,
        product_id: int,
        min_condition: Optional[str] = None,
        max_results: int = 100,
        language_id: Optional[int] = None,
        foil: Optional[bool] = None,
    ) -> list:
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

        try:
            response = self.get_api_call(url=call_url)
        except requests.HTTPError as error:
            raise CardMarketApiError.from_card_market_error(error=error)

        if response.status_code == 204:
            return []

        return response.json()["article"]

    def update_articles_prices(self, articles_data):
        call_url = self.CARD_MARKET_API_URL / "stock"
        response = self.put_api_call(data=articles_data, url=call_url)

        return response.json()
