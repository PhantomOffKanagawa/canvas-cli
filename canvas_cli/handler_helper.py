from functools import wraps
from typing import Any, Optional
from datetime import datetime
import typer
from typing import Optional, TYPE_CHECKING
import typer

if TYPE_CHECKING:
    from canvas_cli.api import CanvasAPI  # only imported for type hints

# ──────────────────────
# DATA SORTING FUNCTIONS
# ──────────────────────

def sort_courses(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Filter out courses without a name (likely access restricted)
    valid_courses = [c for c in courses if 'name' in c]
    
    # Sort by favorite status first, then by name
    sorted_courses = sorted(valid_courses, 
                            key=lambda c: (not c.get('is_favorite', False), c.get('name', '')))
    
    return sorted_courses

def sort_assignments(assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Filter out assignments that cannot be submitted
    valid_assignments = [a for a in assignments if isinstance(a.get('submission_types'), list) and 'online_upload' in a.get('submission_types')] # type: ignore
    
    # Categorize assignments by status
    now = datetime.now().isoformat()
    future_unsubmitted = []  # Not submitted, not past due
    future_submitted = []    # Submitted, not past due
    past_unsubmitted = []    # Not submitted, past due
    past_submitted = []      # Submitted, past due
    locked = []              # Locked assignments
    
    for a in valid_assignments:
        submitted = a.get('has_submitted_submissions', False)
        due_at = a.get('due_at')
        lock_at = a.get('lock_at')
        
        # Check if assignment is locked
        is_locked = (lock_at and lock_at < now)
        
        # Check if assignment is past due
        past_due = (due_at and due_at < now)
        
        # Sort into appropriate category based on due date and submission status
        if is_locked:
            locked.append(a)
        elif not past_due and not submitted:
            future_unsubmitted.append(a)
        elif not past_due and submitted:
            future_submitted.append(a)
        elif past_due and not submitted:
            past_unsubmitted.append(a)
        else:  # past_due and submitted
            past_submitted.append(a)
    
    # Sort each category by due date
    for assignment_list in [future_unsubmitted, future_submitted, past_unsubmitted, past_submitted, locked]:
        assignment_list.sort(key=lambda a: a.get('due_at') or '9999-12-31')
    
    # Combine lists with priority order
    sorted_assignments = future_unsubmitted + future_submitted + past_unsubmitted + past_submitted + locked

    return sorted_assignments

# ──────────────────────
# CONTEXT MANAGER
# ──────────────────────

# Holds all context state (like a dependency container)
class ContextState:
    def __init__(self):
        self.settings = Settings()
        self.api: Optional["CanvasAPI"] = None  # use string form for type hint

# Settings class to hold the verbosity and quietness flags
# This class is used to manage the settings for the CLI application
class Settings:
    verbose: bool = False
    quiet: bool = False

# Accessor for the settings object
def get_settings(ctx: typer.Context) -> Settings:
    return ctx.ensure_object(ContextState).settings

# Function to set the API instance in the context
def get_api(ctx: typer.Context) -> Optional["CanvasAPI"]:
    state = ctx.ensure_object(ContextState)
    if state.api is None:
        raise RuntimeError("API instance is not initialized")
    return state.api

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
