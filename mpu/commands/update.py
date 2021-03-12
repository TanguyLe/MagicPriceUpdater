import logging
import math
from pathlib import Path

import pandas as pd
import typer

from mpu.card_market_client import CardMarketClient
from mpu.utils.log_utils import DATE_FMT
from mpu.utils.pyopenxl_utils import EXCEL_ENGINE
from mpu.stock_handling import MANUAL_PRICE_MARKER

MAX_UPDATES_PER_REQUEST = 100


def main(stock_file_path: Path, yes_to_confirmation: bool):
    logger = logging.getLogger(__name__)
    logger.info("Update starts...")

    stock_parent_path = stock_file_path.parent
    not_updated_file_path = (
        stock_parent_path
        / f"notUpdatedStock-{pd.Timestamp('now').strftime(DATE_FMT)}.xlsx"
    )

    logger.info("Loading stock excel...")
    stock_df = pd.read_excel(io=stock_file_path, engine=EXCEL_ENGINE)
    stock_df = stock_df.fillna("")
    logger.info("Stock loaded.")

    client = CardMarketClient()

    # Handling the 'manual prices'
    # If the price is manual, it overrides the suggested price and goes directly approved
    manual_prices_mask = stock_df["ManualPrice"] != ""
    stock_df.loc[manual_prices_mask, "SuggestedPrice"] = stock_df.loc[
        manual_prices_mask, "ManualPrice"
    ]
    stock_df.loc[manual_prices_mask, "PriceApproval"] = 1
    # The comment is updated if it wasn't already manual
    manual_price_without_marker = manual_prices_mask & (
        ~stock_df["Comments"].str.contains(MANUAL_PRICE_MARKER)
    )
    stock_df.loc[manual_price_without_marker, "Comments"] = (
        stock_df.loc[manual_price_without_marker, "Comments"] + MANUAL_PRICE_MARKER
    )

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
            user_input = typer.prompt(
                f"You are about to update {len(to_update_data)} price(s) for a "
                f"total value difference of {new_price - previous_price:.2f}€. "
                'Type "confirm" to continue or "quit" to leave.'
            )

            if user_input == "quit":
                logger.info("Cancelling the update and leaving mpu")
                return

    logger.info("Updating the article prices...")
    nb_chunks = math.ceil(len(to_update_data) / MAX_UPDATES_PER_REQUEST)
    for i in range(nb_chunks):
        request_start = i * MAX_UPDATES_PER_REQUEST
        client.update_articles_prices(
            articles_data=to_update_data[request_start: request_start + MAX_UPDATES_PER_REQUEST]
        )
    logger.info("Article prices updated.")

    logger.info("Saving the not updated articles...")
    stock_df[~approved_articles_mask].to_excel(
        excel_writer=not_updated_file_path, index=False, engine=EXCEL_ENGINE
    )
    logger.info(f"Not updated articles saved at {not_updated_file_path}.")
    logger.info("Update complete.")
