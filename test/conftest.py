import os

import pandas as pd
import pytest


@pytest.fixture
def test_stock_df():
    df_stock = pd.DataFrame(
        data=[
            "1038903060 16416 BirdsofParadise BirdsofParadise 10E TenthEdition 11 2 NM X     1 1 1 EUR 12 8 0".split(
                " "
            ),
            "969967810 16196 Paladinen-Vec Paladinen-Vec 10E TenthEdition 5.5 2 EX X     1 1 1 EUR  5 1".split(
                " "
            ),
        ],
        columns=[
            "idArticle",
            "idProduct",
            "English Name",
            "Local Name",
            "Exp.",
            "Exp. Name",
            "Price",
            "Language",
            "Condition",
            "Foil?",
            "Signed?",
            "Playset?",
            "Altered?",
            "Comments",
            "Amount",
            "onSale",
            "idCurrency",
            "Currency Code",
            "ManualPrice",
            "SuggestedPrice",
            "PriceApproval"
        ],
    )
    df_stock["Price"] = pd.to_numeric(df_stock["Price"])
    df_stock["Amount"] = pd.to_numeric(df_stock["Amount"])
    df_stock["ManualPrice"] = pd.to_numeric(df_stock["ManualPrice"])
    df_stock["PriceApproval"] = pd.to_numeric(df_stock["PriceApproval"])
    df_stock["RelativePriceDiff"] = 0

    return df_stock


@pytest.fixture
def test_folder_cdir_path(tmp_path):
    new_folder = tmp_path / "testFolder"
    new_folder.mkdir()
    os.chdir(str(new_folder))

    return new_folder
