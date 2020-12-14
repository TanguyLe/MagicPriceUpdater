import logging
import os
from typing import Optional

import pandas as pd
import requests
from authlib.integrations.requests_client import OAuth1Auth
from dicttoxml import dicttoxml
from furl import furl

from mpu.stock_handling import convert_base64_gzipped_string_to_dataframe

logger = logging.getLogger(__name__)


class ApiError(requests.HTTPError):
    """Error when requesting the API"""

    pass


def dict_to_request_xml(my_dict: dict, item_name: str) -> str:
    """Converts a dict to the xml for a request"""
    xml = dicttoxml(
        my_dict,
        custom_root="request",
        attr_type=False,
        item_func=lambda x: item_name,
    )
    return xml.decode("utf-8")


class OAuthAuthenticatedClient:
    """Generic client to handle OAuth auth with fixed credentials from the env"""

    def __init__(self) -> None:
        logger.info(f"Setting up an OAuth client...")
        self.auth = OAuth1Auth(
            client_id=os.environ["CLIENT_KEY"],
            client_secret=os.environ["CLIENT_SECRET"],
            token=os.environ["ACCESS_TOKEN"],
            token_secret=os.environ["ACCESS_SECRET"],
        )
        logger.info(f"Client initialized.")

    def get_api_call(
        self, url: furl, params: Optional[dict] = None
    ) -> requests.Response:
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

    def put_api_call(self, data: dict, url: furl) -> requests.Response:
        url_to_modify = url.copy()
        self.auth.realm = url_to_modify.remove(args=True, fragment=True)
        logger.info(f"Put request to {url}")

        response = requests.put(
            url=url,
            data=dict_to_request_xml(my_dict=data, item_name="article"),
            auth=self.auth,
        )
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
    ) -> dict:
        call_url = self.CARD_MARKET_API_URL / f"/articles/{product_id}"
        if max_results is not None:
            call_url.add(args={"start": 0, "maxResults": max_results})
        if min_condition is not None:
            call_url.add(args={"minCondition": min_condition})

        response = self.get_api_call(url=call_url)

        return response.json()["article"]

    def update_articles_prices(self, articles_data):
        call_url = self.CARD_MARKET_API_URL / "stock"
        response = self.put_api_call(data=articles_data, url=call_url)

        return response.json()
