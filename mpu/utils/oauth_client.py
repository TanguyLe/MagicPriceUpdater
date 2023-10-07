import logging
import os
from pathlib import Path
from typing import Optional

import requests
from authlib.integrations.requests_client import OAuth1Auth
from dicttoxml import dicttoxml
from furl import furl

logger = logging.getLogger(__name__)


class ApiError(requests.HTTPError):
    """Error when requesting the API"""
    @classmethod
    def from_card_market_error(cls, error: requests.HTTPError) -> "ApiError":
        return cls(
            message=f"HTTP error on {error.request.url}: {error} - {error.response.content}",
            code=int(error.response.status_code),
            limit_count=int(error.response.headers["x-request-limit-count"]),
            limit_max=int(error.response.headers["x-request-limit-max"])
        )

    def __init__(self, message: str, code: int, limit_count: int, limit_max: int) -> None:
        self.code = code
        self.limit_count = limit_count
        self.limit_max = limit_max

        super().__init__(message)

    @property
    def exceeded_request_limit(self):
        return self.code == 429 and self.limit_count >= self.limit_max


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

        response = requests.get(url=url, params=params, auth=self.auth)
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            new_error = ApiError.from_card_market_error(error)
            logger.error(str(new_error))
            raise new_error from error
        finally:
            logger.info(f"{response.status_code}: get request to {url}")

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
            new_error = ApiError.from_card_market_error(error)
            logger.error(str(new_error))

            # Debug stuff added in a hurry
            error_debug_path = Path(".").resolve() / "put_api_error_details.xml"
            logger.error("Writing request body to %s", error_debug_path)
            error_debug_path.write_text(data=response.request.body)

            raise new_error from error

        return response
