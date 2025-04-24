from functools import wraps
from typing import Any, Optional
import typer

# Settings class to hold the verbosity and quietness flags
# This class is used to manage the settings for the CLI application
class Settings:
    verbose: bool = False
    quiet: bool = False

# Function to get the settings object from the context
def get_settings(ctx: typer.Context) -> Settings:
    return ctx.ensure_object(Settings)

# Handle sending messages in terms of verbosity and quietness
# This function will check the settings and decide whether to print the message or not
def echo(message: str, ctx: Optional[typer.Context], level: str = "info"):
    if ctx is None:
        print(message)
        return
    
    settings = get_settings(ctx)
    if settings.quiet:
        return
    if settings.verbose or level != "debug":
        print(message)

# Decorator to handle the cascading config resolution
# Get the cascading config value for a given key
def with_config_resolution(*keys):
    """
    Decorator to resolve configuration values for the given keys.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):    
            # Import here to avoid circular import
            from handlers.config_handler import get_cascading_config_value
            for key in keys:
                # For each key in the list, check if it's in kwargs
                if kwargs.get(key) is None:
                    # If not, get the cascading config value for that key
                    kwargs[key] = get_cascading_config_value(key)
            return func(*args, **kwargs)
        return wrapper
    return decorator
