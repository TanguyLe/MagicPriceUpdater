import enum
import sys
from pathlib import Path

import typer

from mpu.getstock import main as main_getstock
from mpu.stats import main as main_stats

# Extensions
sys.path.append(str(Path(__file__).parent / "MPUStrategies"))
from mpu_strategies.compute_current_price import CurrentPriceComputer
from mpu_strategies.price_update import PriceUpdater

app = typer.Typer()

CurrentPriceStrat = enum.Enum(
    "CurrentPriceStrat",
    {strat: strat for strat in CurrentPriceComputer.get_available_strategies()},
)
PriceUpdaterStrat = enum.Enum(
    "PriceUpdaterStrat",
    {strat: strat for strat in PriceUpdater.get_available_strategies()},
)


@app.command()
def getstock(
    current_price_strategy: CurrentPriceStrat,
    price_update_strategy: PriceUpdaterStrat,
    strategies_options_path: Path = typer.Option(
        None,
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
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the output. Default is the current directory",
    ),
    force_download: bool = typer.Option(
        False, help="Force download the market extract."
    ),
    parallel_execution: bool = typer.Option(
        False, help="Parallelize the calls to the card market API."
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
def update():
    raise NotImplementedError("update is not implemented yet.")


@app.command()
def stats(
    output_path: Path = typer.Option(
        Path.cwd(),
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Path where to save the output. Default is the current directory",
    ),
):
    main_stats(output_path=output_path)


if __name__ == "__main__":
    app()
