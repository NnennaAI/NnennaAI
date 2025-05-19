import typer
from cli.commands import init, run, assess, scan

app = typer.Typer(help="🧠 nai: CLI for the NnennaAI framework")

# Register subcommands
app.add_typer(init.app, name="init")
app.add_typer(run.app, name="run")
app.add_typer(assess.app, name="assess")
app.add_typer(scan.app, name="scan")

if __name__ == "__main__":
    app()
