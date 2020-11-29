from pathlib import Path

import os
import typer

from mpu.getstock import main

app = typer.Typer()


@app.command()
def getstock(
        current_price_strategy: str = typer.Argument(...),
        price_update_strategy: str = typer.Argument(...),
        market_extract_path: Path = typer.Option(
            os.getcwd(),
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
            help="Path where to save the market extract. Default is the current directory"
        ),
        output_path: Path = typer.Option(
            os.getcwd(),
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
            help="Path where to save the output. Default is the current directory"
        ),
        force_download: bool = typer.Option(False, help="Force download the market extract.")
):
    main(
        current_price_strategy=current_price_strategy,
        price_update_strategy=price_update_strategy,
        market_extract_path=market_extract_path,
        output_path=output_path,
        force_update=force_download
    )


@app.command()
def update():
    raise NotImplementedError("update is not implemented yet.")


@app.command()
def stats():
    raise NotImplementedError("stats is not implemented yet.")


if __name__ == "__main__":
    app()
