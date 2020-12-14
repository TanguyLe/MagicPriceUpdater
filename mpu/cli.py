from pathlib import Path

import typer

from mpu.getstock import main as main_getstock
from mpu.log_utils import log_setup
from mpu.stats import main as main_stats
from mpu.stock_handling import get_stock_file_path
from mpu.strategies_utils import CurrentPriceStrat, PriceUpdaterStrat
from mpu.update import main as main_update

app = typer.Typer()


@app.command()
@log_setup
def getstock(
    current_price_strategy: CurrentPriceStrat,
    price_update_strategy: PriceUpdaterStrat,
    strategies_options_path: Path = typer.Option(
        None,
        "--strategies-options-path",
        "-sop",
        exists=True,
        file_okay=True,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path of the file to configure the strategies, if not provided not parameters are used",
    ),
    market_extract_path: Path = typer.Option(
        Path.cwd(),
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
        Path.cwd(),
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
    force_download: bool = typer.Option(
        False, "--force-download", "-f", help="Force download the market extract."
    ),
    parallel_execution: bool = typer.Option(
        True,
        "--parallel-execution",
        "-p",
        help="Parallelize the calls to the card market API.",
    ),
):
    main_getstock(
        current_price_strategy=current_price_strategy.value,
        price_update_strategy=price_update_strategy.value,
        strategies_options_path=strategies_options_path,
        market_extract_path=market_extract_path,
        output_path=output_path,
        force_update=force_download,
        parallel_execution=parallel_execution,
    )


@app.command()
@log_setup
def update(
    stock_file_path: Path = typer.Option(
        get_stock_file_path(folder_path=Path.cwd()),
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
@log_setup
def stats(
    output_path: Path = typer.Option(
        Path.cwd(),
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
) -> None:
    main_stats(output_path=output_path)


if __name__ == "__main__":
    app()
