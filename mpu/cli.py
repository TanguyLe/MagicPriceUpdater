from pathlib import Path

import typer

from mpu.commands.getstock import main as main_getstock
from mpu.utils.log_utils import set_log_conf
from mpu.commands.stats import get_stats_file_path
from mpu.commands.stats import main as main_stats
from mpu.stock_io import get_stock_file_path
from mpu.utils.strategies_utils import CurrentPriceStrat, PriceUpdaterStrat
from mpu.commands.update import main as main_update

app = typer.Typer()


__version__ = "0.4.2"


@app.command()
def getstock(
        current_price_strategy: CurrentPriceStrat,
        price_update_strategy: PriceUpdaterStrat,
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
    main_getstock(
        current_price_strategy=current_price_strategy.value,
        price_update_strategy=price_update_strategy.value,
        config_path=config_path,
        market_extract_path=market_extract_path,
        output_path=output_path,
        force_update=force_download,
        parallel_execution=not no_parallel_execution,
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
        version: bool = typer.Option(None, "-v", "--version", callback=version_callback, is_eager=True),
):
    set_log_conf(log_path=Path.cwd())


def main():
    app()


if __name__ == "__main__":
    main()
