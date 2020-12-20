import logging
from pathlib import Path

import pandas as pd

from mpu.card_market_client import CardMarketClient


def main(stock_file_path: Path, yes_to_confirmation: bool):
    logger = logging.getLogger(__name__)
    logger.info("Update stats...")

    stock_parent_path = stock_file_path.parent
    not_updated_file_path = (
        stock_parent_path / f"notUpdatedStock-{pd.Timestamp('now').isoformat()}.xlsx"
    )

    stock_df = pd.read_excel(io=stock_file_path, engine="openpyxl")

    client = CardMarketClient()
    approved_articles_mask = stock_df["PriceApproval"] == 1

    stock_to_update = stock_df.loc[approved_articles_mask]

    previous_price = (stock_to_update["Price"] * stock_to_update["Amount"]).sum()
    new_price = (stock_to_update["SuggestedPrice"] * stock_to_update["Amount"]).sum()

    stock_to_update = stock_to_update[
        ["idArticle", "Comments", "Amount", "SuggestedPrice"]
    ]
    stock_to_update = stock_to_update.rename(
        columns={"SuggestedPrice": "price", "Comments": "comments", "Amount": "count"}
    )

    to_update_data = list(stock_to_update.T.to_dict().values())

    if not yes_to_confirmation:
        user_input = ""
        while user_input != "confirm":
            print(
                f"You are about to update {len(to_update_data)} price(s) for a "
                f"total value difference of {previous_price - new_price:.2f}€. "
                'Type "confirm" to continue or "quit" to leave.'
            )
            user_input = input()

            if user_input == "quit":
                logger.info("Cancelling the update and leaving mpu")
                return

    logger.info("Updating the article prices...")
    client.update_articles_prices(articles_data=to_update_data)
    logger.info("Article prices updated.")

    logger.info("Saving the not updated articles...")
    stock_df[~approved_articles_mask].to_excel(
        excel_writer=not_updated_file_path, index=False
    )
    logger.info(f"Not updated articles saved at {not_updated_file_path}.")
    logger.info("Update complete.")
