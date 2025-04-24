import typer
from typer import Typer, Argument, Option
from typing import Optional
from args.config_args import config_app

app = Typer(
    invoke_without_command=True,
    no_args_is_help=True,
    help="Configure settings for the CLI",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# ──────────────────────
# SUBCOMMANDS
# ──────────────────────

app.add_typer(config_app, name="config")


# ────────────────────
# MAIN FUNCTION
# ────────────────────

def main():
    app()

if __name__ == "__main__":
    app()
