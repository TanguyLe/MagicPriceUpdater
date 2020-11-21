import logging
import statistics
import os
from typing import Optional, List

import pandas as pd
from authlib.integrations.requests_client import OAuth1Auth
from furl import furl
import requests

from mpu.stock_handling import convert_base64_gzipped_string_to_dataframe


logger = logging.getLogger(__name__)


class ApiError(requests.HTTPError):
    """Error when requesting the API"""
    pass


class OAuthAuthenticatedClient:
    """Generic client to handle OAuth auth with fixed credentials from the env"""
    def __init__(self) -> None:
        self.auth = OAuth1Auth(
            client_id=os.environ["CLIENT_KEY"],
            client_secret=os.environ["CLIENT_SECRET"],
            token=os.environ["ACCESS_TOKEN"],
            token_secret=os.environ["ACCESS_SECRET"],
        )

    def _get_api_call(self, url: furl, params: Optional[dict] = None) -> requests.Response:
        url_to_modify = url.copy()
        self.auth.realm = url_to_modify.remove(args=True, fragment=True)
        logger.info(f"Get request to {url}")

        response = requests.get(url=url, params=params, auth=self.auth)
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            err_msg = f"HTTP error on {url}: {error}"
            logger.error(err_msg)
            raise ApiError(err_msg) from error

        return response


class CardMarketClient(OAuthAuthenticatedClient):
    CARD_MARKET_API_URL = furl("https://api.cardmarket.com/ws/v2.0/output.json")

    def get_stock_df(self) -> pd.DataFrame:
        response = self._get_api_call(url=self.CARD_MARKET_API_URL / "stock/file")
        stock_string = response.json()["stock"]

        return convert_base64_gzipped_string_to_dataframe(b64_zipped_string=stock_string)

    def get_product_info(self, product_id: int) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/products/{product_id}"
        response = self._get_api_call(url=call_url)

        return response.json()

    def get_product_articles(
            self, product_id: int, min_condition: Optional[str] = None, max_results: int = 100
    ) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/articles/{product_id}"
        if max_results is not None:
            call_url.add(args={"start": 0, "maxResults": max_results})
        if min_condition is not None:
            call_url.add(args={"minCondition": min_condition})

        response = self._get_api_call(url=call_url)

        return response.json()["article"]

    def update_product_prices(self):
        raise NotImplementedError("Not implemented yet")
