import os

import pandas as pd
import pytest
import requests_mock
from typer.testing import CliRunner

from mpu.cli import app
from mpu.utils.pyopenxl_utils import EXCEL_ENGINE, format_and_save_df
from mpu.excel_formats import STOCK_COLUMNS_FORMAT

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


@pytest.fixture
def save_stock_file(test_folder_cdir_path):
    def _save_stock_file(stock_df):
        new_stock_file_path = test_folder_cdir_path / "stock.xlsx"

        writer = pd.ExcelWriter(path=str(new_stock_file_path), engine=EXCEL_ENGINE)
        stock_df.to_excel(excel_writer=writer, index=False, engine=EXCEL_ENGINE)

        format_and_save_df(
            df=stock_df, writer=writer, format_config=STOCK_COLUMNS_FORMAT
        )

        return new_stock_file_path

    return _save_stock_file


def test_integration_update(mocker, save_stock_file, test_stock_df):
    new_stock_file_path = save_stock_file(stock_df=test_stock_df)
    os.chdir(str(new_stock_file_path.parent))

    mocker.patch("mpu.update.typer.prompt", return_value="confirm")

    with requests_mock.Mocker() as r_mock:
        r_mock.put(
            "https://api.cardmarket.com/ws/v2.0/output.json/stock",
            json={"stock": "placeholder"},
        )

        result = runner.invoke(app, ["update"])

    assert result.exit_code == 0
    assert len(r_mock.request_history) == 1
    assert r_mock.request_history[0].text == (
        '<?xml version="1.0" encoding="UTF-8" ?>'
        + (
            "   <request>"
            "       <article>"
            "           <idArticle>1038903060</idArticle>"
            "           <comments>&lt;M&gt;</comments>"
            "           <count>1</count>"
            "           <price>12.0</price>"
            "       </article>"
            "       <article>"
            "          <idArticle>969967810</idArticle>"
            "          <comments></comments>"
            "          <count>1</count>"
            "          <price>5</price>"
            "      </article>"
            "  </request>"
        ).replace(" ", "")
    )


def test_integration_update_multiple_requests(mocker, test_stock_df, save_stock_file):
    new_df_stock = pd.concat([test_stock_df] * 501).reset_index(drop=True)

    new_stock_file_path = save_stock_file(stock_df=new_df_stock)
    os.chdir(str(new_stock_file_path.parent))

    mocker.patch("mpu.update.typer.prompt", return_value="confirm")

    with requests_mock.Mocker() as r_mock:
        r_mock.put(
            "https://api.cardmarket.com/ws/v2.0/output.json/stock",
            json={"stock": "placeholder"},
        )

        result = runner.invoke(app, ["update"])

    assert result.exit_code == 0
    assert len(r_mock.request_history) == 11
    assert r_mock.request_history[0].text == (
        '<?xml version="1.0" encoding="UTF-8" ?>'
        + (
            "   <request>"
            + (
                "       <article>"
                "           <idArticle>1038903060</idArticle>"
                "           <comments>&lt;M&gt;</comments>"
                "           <count>1</count>"
                "           <price>12.0</price>"
                "       </article>"
                "       <article>"
                "       <idArticle>969967810</idArticle>"
                "       <comments></comments>"
                "       <count>1</count>"
                "       <price>5</price>"
                "   </article>"
            )
            * 50
            + "</request>"
        ).replace(" ", "")
    )
    assert r_mock.request_history[-1].text == (
        '<?xml version="1.0" encoding="UTF-8" ?>'
        + (
            "   <request>"
            + (
                "       <article>"
                "           <idArticle>1038903060</idArticle>"
                "           <comments>&lt;M&gt;</comments>"
                "           <count>1</count>"
                "           <price>12.0</price>"
                "       </article>"
                "       <article>"
                "       <idArticle>969967810</idArticle>"
                "       <comments></comments>"
                "       <count>1</count>"
                "       <price>5</price>"
                "   </article>"
            )
            + "</request>"
        ).replace(" ", "")
    )
