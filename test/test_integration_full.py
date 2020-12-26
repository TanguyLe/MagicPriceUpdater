import os
import pytest

import pandas as pd
import requests_mock
from typer.testing import CliRunner


DF_STOCK = pd.DataFrame(
    data=[
            "1038903060 16416 BirdsofParadise BirdsofParadise 10E TenthEdition 11 2 NM X     1 1 1 EUR".split(' '),
            "969967525 16194 NomadMythmaker NomadMythmaker 10E TenthEdition 3.5 2 GD X     1 1 1 EUR".split(' '),
            "969967810 16196 Paladinen-Vec Paladinen-Vec 10E TenthEdition 5.5 2 EX X     1 1 1 EUR".split(' ')

    ],
    columns=["idArticle", "idProduct", "English Name", "Local Name", "Exp.", "Exp. Name", "Price", "Language", "Condition", "Foil?", "Signed?", "Playset?", "Altered?", "Comments", "Amount", "onSale", "idCurrency", "Currency Code"]
)
DF_STOCK["Price"] = pd.to_numeric(DF_STOCK["Price"])
DF_STOCK["Amount"] = pd.to_numeric(DF_STOCK["Amount"])

# Doing more or less the same things as the algo itself, with the current mocks
DF_STOCK_OUTPUT = DF_STOCK.copy()
DF_STOCK_OUTPUT["ManualPrice"] = float("nan")
DF_STOCK_OUTPUT["SuggestedPrice"] = 10
DF_STOCK_OUTPUT["PriceApproval"] = 1
DF_STOCK_OUTPUT = DF_STOCK_OUTPUT.reindex([1, 2, 0])
DF_STOCK_OUTPUT["RelativePriceDiff"] = [185.71, 81.82, -9.09]


runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_settings_env_vars(mocker):
    mocker.patch.dict(os.environ, {"CLIENT_KEY": "my-client-key", "CLIENT_SECRET": "my-client-secret", "ACCESS_TOKEN": "my-access-token", "ACCESS_SECRET": "my-access-secret"})


def test_integration_gestock(tmp_path, mocker):
    mocker.patch("mpu.card_market_client.convert_base64_gzipped_string_to_dataframe", return_value=DF_STOCK)
    compute_current_price_mock = mocker.patch("mpu.getstock.CurrentPriceComputer")
    compute_current_price_mock.return_value.get_current_price_from_market_extract = mocker.Mock(return_value=10)
    new_folder = (tmp_path / "testFolder")
    new_folder.mkdir()
    os.chdir(str(new_folder))

    from mpu.cli import app

    with requests_mock.Mocker() as r_mock:
        r_mock.get("https://api.cardmarket.com/ws/v2.0/output.json/stock/file", json={"stock": "placeholder"})
        r_mock.get("https://api.cardmarket.com/ws/v2.0/output.json/articles/16416?start=0&maxResults=100&minCondition=EX", json={"article": "placeholder"})
        r_mock.get("https://api.cardmarket.com/ws/v2.0/output.json/articles/16194?start=0&maxResults=100&minCondition=EX", json={"article": "placeholder"})
        r_mock.get("https://api.cardmarket.com/ws/v2.0/output.json/articles/16196?start=0&maxResults=100&minCondition=EX", json={"article": "placeholder"})
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16416",
            json={"stock": "placeholder"})
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16194",
            json={"stock": "placeholder"})
        r_mock.get(
            "https://api.cardmarket.com/ws/v2.0/output.json/products/16196",
            json={"stock": "placeholder"})

        result = runner.invoke(app, ["getstock", "market_and_lower", "initial", "--no-parallel-execution"])

    assert result.exit_code == 0
    assert (new_folder / "market_extract").exists()
    assert (new_folder / "market_extract" / "16416.json").exists()
    assert (new_folder / "market_extract" / "16194.json").exists()
    assert (new_folder / "market_extract" / "16196.json").exists()
    DF_STOCK_OUTPUT.to_excel("test.xlsx", index=False)
    pd.testing.assert_frame_equal(pd.read_excel(new_folder / "stock.xlsx", engine="openpyxl"), pd.read_excel("test.xlsx", engine="openpyxl"))
    # TODO Run black & isort
