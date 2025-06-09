import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import pandas as pd
import requests
from furl import furl

from mpu.stock_io import convert_base64_gzipped_string_to_dataframe
from mpu.utils.oauth_client import OAuthAuthenticatedClient

logger = logging.getLogger(__name__)

MAX_WAIT_TIME = 60 * 90
POLL_INTERVAL = 30
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
            limit_max=int(limit_max) if limit_max is not None else None,
        )

    def __init__(
        self,
        message: str,
        code: int,
        limit_count: Optional[int],
        limit_max: Optional[int],
    ) -> None:
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
        """Get stock data using the new exports/stock endpoint."""
        logger.info("Getting stock data from Card Market...")
        
        download_url = self._get_download_url()
        
        return self._download_and_process_stock_file(download_url)

    def _get_download_url(self) -> str:
        """Get download URL by finding or creating an export and waiting for it to finish."""
        exports_data = self._get_exports()
        export = self._find_or_create_export(exports_data=exports_data)
        
        if export.get("status") == "finished":
            logger.info(f"Export {export.get('idRequest')} is ready.")
            return export["url"]
        
        return self._wait_for_export_url(export_id=export.get("idRequest"))

    def _get_exports(self) -> dict:
        """Get current exports from API."""
        response = self.get_api_call(url=self.CARD_MARKET_API_URL / "exports/stock")
        return response.json()

    def _find_or_create_export(self, exports_data: dict) -> dict:
        """Find a usable export or trigger a new one. Always returns export data."""
        exports = exports_data["stockExports"]
        logger.info(f"Found {len(exports)} exports")
        
        recent_exports = self._filter_recent_exports(exports)
        logger.info(f"Found {len(recent_exports)} recent exports (< 2 hour old)")
        
        for export in recent_exports:
            if export.get("status") == "finished":
                export_id = export.get("idRequest")
                logger.info(f"Found finished export {export_id}.")
                return export
        
        for export in recent_exports:
            status = export.get("status")
            if status == "pending":
                export_id = export.get("idRequest")
                logger.info(f"Found ongoing export {export_id}, will wait for it.")
                return export
        
        return self._trigger_new_export()

    def _filter_recent_exports(self, exports: list) -> list:
        """Filter exports to only include those less than 2 hour old."""
        recent_exports = []
        current_time = datetime.now(timezone.utc)
        one_hour = timedelta(hours=2)
        
        for export in exports:
            started_at = export.get("startedAt")
            if not started_at:
                continue
            
            try:
                export_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                # Ensure export_time is timezone-aware
                if export_time.tzinfo is None:
                    export_time = export_time.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse timestamp for export {export.get('idRequest')}: {started_at} - {e}")
                continue
            
            age = current_time - export_time
            
            if age < one_hour:
                recent_exports.append(export)
  
        return recent_exports

    def _trigger_new_export(self) -> str:
        """Trigger a new export and return its ID."""
        logger.info("Triggering new stock export...")
        
        export_url = self.CARD_MARKET_API_URL / "exports/stock"
        export_url.add(args={"idGame": 1})
        
        try:
            response = self.post_api_call(url=export_url, data={})
        except requests.HTTPError as error:          
            raise CardMarketApiError.from_card_market_error(error=error)

        result = response.json()
        export_id = result.get("idRequest")
        logger.info(f"New export {export_id} triggered")
        return result

    def _wait_for_export_url(self, export_id: str) -> str:
        """Wait for an export to finish and return the download URL."""
        logger.info(f"Waiting for export {export_id} to finish...")
        start_time = time.time()
        
        while time.time() - start_time < MAX_WAIT_TIME:
            exports_data = self._get_exports()
            
            for export in exports_data.get("stockExports", []):
                current_id = export.get("idRequest")
                
                if current_id != export_id:
                    continue
                
                if export.get("status") == "finished":
                    logger.info(f"Export {current_id} finished")
                    return export["url"]
            
            logger.info(f"Export still processing, waiting {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)
        
        raise TimeoutError(f"Export did not complete within {MAX_WAIT_TIME} seconds")

    def _download_and_process_stock_file(self, download_url: str) -> pd.DataFrame:
        """Download and process the stock file from the provided URL."""
        logger.info("Downloading stock file...")
        
        try:
            response = requests.get(download_url)
            response.raise_for_status()
        except requests.HTTPError as error:
            logger.error(f"Failed to download stock file: {error}")
            raise CardMarketApiError.from_card_market_error(error=error)
        
        try:
            stock_data = response.json()
        except ValueError as error:
            logger.error(f"Failed to parse JSON response: {error}")
            raise
        
        logger.info(f"Downloaded data keys: {list(stock_data.keys())}")
        
        logger.info("Processing article data directly")
        result = self._normalize_article_data(stock_data["article"])
      
        logger.info(f"Stock retrieved and processed. Shape: {result.shape}")
        return result

    def _normalize_article_data(self, articles: list) -> pd.DataFrame:
        """Normalize article data to match expected CSV format with exact columns."""
        # Define the exact columns we want in the exact order
        expected_columns = [
            "idArticle", "idProduct", "English Name", "Local Name", "Exp.", "Price", 
            "Language", "Condition", "Foil?", "Signed?", "Comments", "Amount", "onSale"
        ]
        
        normalized_articles = []
        
        for article in articles:
            normalized_article = {}
            
            normalized_article["idArticle"] = article.get("idArticle", "")
            normalized_article["idProduct"] = article.get("idProduct", "")
            
            # Extract names and expansion from product object
            if "product" in article and isinstance(article["product"], dict):
                normalized_article["English Name"] = article["product"].get("enName", "")
                normalized_article["Local Name"] = article["product"].get("locName", "")
                normalized_article["Exp."] = article["product"].get("abbreviation", "")
            else:
                normalized_article["English Name"] = ""
                normalized_article["Local Name"] = ""
                normalized_article["Exp."] = ""
            
            normalized_article["Price"] = article.get("price", "")
            
            # Extract Language ID from language object
            if "language" in article and isinstance(article["language"], dict):
                normalized_article["Language"] = article["language"].get("idLanguage", "")
            else:
                normalized_article["Language"] = article.get("language", "")
            
            normalized_article["Condition"] = article.get("condition", "")
            normalized_article["Signed?"] = article.get("isSigned", "")
            normalized_article["Foil?"] = article.get("isFoil", "")
            normalized_article["Comments"] = article.get("comments", "")
            normalized_article["Amount"] = article.get("count", "")
            normalized_article["onSale"] = article.get("onSale", "")            
            
            normalized_articles.append(normalized_article)
        
        # Create DataFrame with exact columns in exact order
        df = pd.DataFrame(normalized_articles)

        df["Foil?"] = df["Foil?"].replace(
            {"True": "X", "False": "", True: "X", False: ""}
        ).astype(str)
        df["Signed?"] = df["Signed?"].replace(
            {"True": "X", "False": "", True: "X", False: ""}
        ).astype(str)
        
        # Ensure all expected columns exist and are in the right order
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        
        return df[expected_columns].set_index("idArticle")

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
