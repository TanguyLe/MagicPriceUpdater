import logging
from pathlib import Path

from mpu.card_market_client import CardMarketClient
from mpu.stock_io import get_stock_file_path


def main(
    output_path: Path,
):
    logger = logging.getLogger(__name__)
    logger.info("Starting getstock...")

    stock_output_path = get_stock_file_path(folder_path=output_path, csv=True)

    logger.info(f"Setting up the client...")
    client = CardMarketClient()
    logger.info(f"Client initialized.")

    stock_df = client.get_stock_df()

    # Saves the result
    logger.info("Saving the stock...")
    stock_df.to_csv(stock_output_path)
    logger.info(f"Stock saved at {stock_output_path}.")

    logger.info("getstock complete.")
