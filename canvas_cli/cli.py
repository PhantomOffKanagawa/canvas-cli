import typer
from typer import Typer, Argument, Option
from typing import Optional
from args.config_args import config_app
from args.push_args import push_app
from args.init_args import init_app
from canvas_cli.handler_helper import ContextState
from canvas_cli.api import CanvasAPI

app = Typer(
    invoke_without_command=True,
    no_args_is_help=True,
    help="Configure settings for the CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@app.callback()
def app_callback(
    ctx: typer.Context,
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = Option(False, "--quiet", "-q", help="Suppress output"),
):
    state = ctx.ensure_object(ContextState)
    state.settings.verbose = verbose
    state.settings.quiet = quiet
    state.api = CanvasAPI(ctx=ctx)

# ──────────────────────
# SUBCOMMANDS
# ──────────────────────

app.add_typer(config_app, name="config")

app.add_typer(push_app, name="push")

app.add_typer(init_app, name="init")


# ────────────────────
# MAIN FUNCTION
# ────────────────────

def main():
    app()

if __name__ == "__main__":
    app()
