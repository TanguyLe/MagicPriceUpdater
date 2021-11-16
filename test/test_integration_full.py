import os

import pandas as pd
import pytest
import requests_mock
from typer.testing import CliRunner

from mpu.cli import app
from mpu.utils.pyopenxl_utils import EXCEL_ENGINE


@pytest.fixture
def test_stock_output_df(test_stock_df):
    # Doing more or less the same things as the algo itself, with the current mocks
    stock_output_df = test_stock_df.copy()
    stock_output_df["ManualPrice"] = float("nan")
    stock_output_df["SuggestedPrice"] = 10
    stock_output_df["PriceApproval"] = 1
    stock_output_df = stock_output_df.reindex([1, 0])
    stock_output_df["RelativePriceDiff"] = [81.82, -9.09]

    return stock_output_df


runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_settings_env_vars(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "CLIENT_KEY": "my-client-key",
            "CLIENT_SECRET": "my-client-secret",
            "ACCESS_TOKEN": "my-access-token",
            "ACCESS_SECRET": "my-access-secret",
        },
    )


def test_integration_gestock(
    test_folder_cdir_path, test_stock_df, test_stock_output_df, mocker
):
    mocker.patch(
        "mpu.card_market_client.convert_base64_gzipped_string_to_dataframe",
        return_value=test_stock_df.drop("ManualPrice", axis="columns"),
    )
    compute_current_price_mock = mocker.patch("mpu.getstock.CurrentPriceComputer")
    compute_current_price_mock.return_value.get_current_price_from_market_extract = (
        mocker.Mock(return_value=10)
    )

    with requests_mock.Mocker() as r_mock:
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/stock/file",
            json={"stock": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/articles/16416?start=0&maxResults=100&minCondition=EX",
            json={"article": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/articles/16194?start=0&maxResults=100&minCondition=EX",
            json={"article": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/articles/16196?start=0&maxResults=100&minCondition=EX",
            json={"article": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16416",
            json={"stock": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16194",
            json={"stock": "placeholder"},
        )
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16196",
            json={"stock": "placeholder"},
        )

        result = runner.invoke(
            app, ["getstock", "market_and_lower", "initial", "--no-parallel-execution"]
        )

    assert result.exit_code == 0
    assert (test_folder_cdir_path / "market_extract").exists()
    assert (test_folder_cdir_path / "market_extract" / "16416.json").exists()
    assert (test_folder_cdir_path / "market_extract" / "16196.json").exists()
    # Is valid because we changed the current directory before
    test_stock_output_df.to_excel("test.xlsx", index=False, engine=EXCEL_ENGINE)
    pd.testing.assert_frame_equal(
        left=pd.read_excel("stock.xlsx", engine=EXCEL_ENGINE),
        right=pd.read_excel("test.xlsx", engine=EXCEL_ENGINE),
    )
