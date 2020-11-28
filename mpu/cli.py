import typer

from mpu.getstock import main

app = typer.Typer()


@app.command()
def getstock():
    main()


@app.command()
def update():
    raise NotImplementedError("update is not implemented yet.")


@app.command()
def stats():
    raise NotImplementedError("stats is not implemented yet.")


if __name__ == "__main__":
    app()
