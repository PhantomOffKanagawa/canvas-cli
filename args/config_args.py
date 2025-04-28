import typer
from handlers.config_handler import handle_config_tui
from typer import Typer, Argument, Option
from typing import Optional
from handlers.config_handler import handle_config_get, handle_config_set, handle_config_unset, handle_config_list

config_app = Typer(
    invoke_without_command=True,
    no_args_is_help=True,
    help="Configure settings for the CLI",
)

@config_app.command("get")
def config_get(
    ctx: typer.Context,
    key: str = Argument(None, help="Configuration key to get"),
    global_: bool = Option(False, "--global", "-g", help="Use global config"),
    local: bool = Option(False, "--local", help="Use local config"),
):
    "Get the value for a given config key"
    handle_config_get(ctx=ctx, key=key, global_=global_, local=local)


@config_app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = Argument(..., help="Configuration key to set"),
    value: str = Argument(..., help="Value to assign to the key"),
    global_: bool = Option(False, "--global", "-g", help="Use global config"),
    local: bool = Option(False, "--local", help="Use local config"),
):
    "Set a config key to a given value"
    handle_config_set(ctx=ctx, key=key, value=value, global_=global_, local=local)


@config_app.command("unset")
def config_unset(
    ctx: typer.Context,
    key: str = Argument(..., help="Configuration key to unset"),
    global_: bool = Option(False, "--global", "-g", help="Use global config"),
    local: bool = Option(False, "--local", help="Use local config"),
):
    "Unset a config key"
    handle_config_unset(ctx=ctx, key=key, global_=global_, local=local)


@config_app.command("list")
def config_list(
    ctx: typer.Context,
    global_: bool = Option(False, "--global", "-g", help="Use global config"),
    local: bool = Option(False, "--local", help="Use local config"),
    show_origin: bool = Option(False, "--show-origin", help="Show the origin of each config key"),
    show_scope: bool = Option(False, "--show-scope", help="Show the scope of each config key"),
):
    "List all config keys and values"
    handle_config_list(ctx=ctx, global_=global_, local=local, show_origin=show_origin, show_scope=show_scope)


@config_app.command("tui")
def config_tui(
    ctx: typer.Context,
    global_: bool = typer.Option(False, "--global", help="Set in global config (default)"),
    local: bool = typer.Option(False, "--local", help="Set in local config"),
):
    """Customize and configure the TUI (emoji, fallback, etc)"""
    handle_config_tui(ctx, global_, local)