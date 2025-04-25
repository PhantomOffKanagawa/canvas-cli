from typing import Any, Optional
import typer
from canvas_cli.api import CanvasAPI

# Holds all context state (like a dependency container)
class ContextState:
    def __init__(self):
        self.settings = Settings()
        self.api: Optional[CanvasAPI] = None

# Settings class to hold the verbosity and quietness flags
# This class is used to manage the settings for the CLI application
class Settings:
    verbose: bool = False
    quiet: bool = False

# Accessor for the settings object
def get_settings(ctx: typer.Context) -> Settings:
    return ctx.ensure_object(ContextState).settings

# Function to set the API instance in the context
def get_api(ctx: typer.Context) -> CanvasAPI:
    state = ctx.ensure_object(ContextState)
    if state.api is None:
        raise RuntimeError("API instance is not initialized")
    return state.api