from pathlib import Path

import typer

from mpu.commands.calculate import main as main_calculate
from mpu.commands.getdata import main as main_getdata
from mpu.commands.getstock import main as main_getstock
from mpu.commands.stats import get_stats_file_path
from mpu.commands.stats import main as main_stats
from mpu.commands.update import main as main_update
from mpu.stock_io import get_stock_file_path
from mpu.utils.strategies_utils import CurrentPriceStrat, PriceUpdaterStrat

app = typer.Typer()


__version__ = "0.9.1"


@app.command()
def getstock(
    output_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--output-path",
        "-op",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the output. Default is the current directory",
    ),
):
    main_getstock(
        output_path=output_path,
    )


@app.command()
def getdata(
    input_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--input-path",
        "-ip",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to load the output from getstock. Default is the current directory",
    ),
    config_path: Path = typer.Option(
        ...,
        "--config-path",
        "-cp",
        exists=True,
        file_okay=True,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path of the file to configure mpu",
    ),
    market_extract_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--market-extract-path",
        "--mep",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the market extract. Default is the current directory",
    ),
    minimum_price: float = typer.Option(
        0, "--minimum-price", "-m", help="Minimum price to keep for articles to keep."
    ),
    force_download: bool = typer.Option(
        False, "--force-download", "-f", help="Force download the market extract."
    ),
    no_parallel_execution: bool = typer.Option(
        False,
        "--no-parallel-execution",
        "-np",
        help="Don't parallelize the calls to the card market API.",
    ),
):
    main_getdata(
        input_path=input_path,
        config_path=config_path,
        market_extract_path=market_extract_path,
        minimum_price=minimum_price,
        force_update=force_download,
        parallel_execution=not no_parallel_execution,
    )


@app.command()
def calculate(
    current_price_strategy: CurrentPriceStrat,
    price_update_strategy: PriceUpdaterStrat,
    input_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--input-path",
        "-ip",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to load the output from getstock. Default is the current directory",
    ),
    config_path: Path = typer.Option(
        ...,
        "--config-path",
        "-cp",
        exists=True,
        file_okay=True,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path of the file to configure mpu",
    ),
    market_extract_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--market-extract-path",
        "--mep",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the market extract. Default is the current directory",
    ),
    output_path: Path = typer.Option(
        lambda: Path.cwd(),
        "--output-path",
        "-op",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the output. Default is the current directory",
    ),
    minimum_price: float = typer.Option(
        0, "--minimum-price", "-m", help="Minimum price to keep for articles to keep."
    ),
):
    main_calculate(
        input_path=input_path,
        current_price_strategy=current_price_strategy.value,
        price_update_strategy=price_update_strategy.value,
        config_path=config_path,
        market_extract_path=market_extract_path,
        output_path=output_path,
        minimum_price=minimum_price,
    )


@app.command()
def update(
    stock_file_path: Path = typer.Option(
        lambda: get_stock_file_path(folder_path=Path.cwd()),
        "--stock-file-path",
        "-sfp",
        exists=True,
        file_okay=True,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to get the stock df. Default is the current directory's 'stock.csv'",
    ),
    yes_to_confirmation: bool = typer.Option(
        False,
        "--yes-to-confirmation",
        "-y",
        help="Prevents confirmation prompt from appearing.",
    ),
) -> None:
    main_update(
        stock_file_path=stock_file_path, yes_to_confirmation=yes_to_confirmation
    )


@app.command()
def stats(
    stats_file_path: Path = typer.Option(
        lambda: get_stats_file_path(folder_path=Path.cwd()),
        "--stats-file-path",
        "-sfp",
        exists=False,
        file_okay=True,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to get the stats df. Default is the current directory's 'stockStats.csv'",
    ),
) -> None:
    main_stats(stats_file_path=stats_file_path)


def version_callback(value: bool):
    if value:
        typer.echo(f"mpu: v{__version__}")
        raise typer.Exit()


@app.callback()
def main_typer(
    version: bool = typer.Option(
        None, "-v", "--version", callback=version_callback, is_eager=True
    ),
):
    pass


def main():
    app()


if __name__ == "__main__":
    main()
