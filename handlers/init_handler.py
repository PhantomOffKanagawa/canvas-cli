import json
import typer
from typing import Optional
from canvas_cli.handler_helper import echo
from handlers.config_handler import get_key, load_config, save_config
from canvas_cli.constants import LOCAL_CONFIG_PATH
from canvas_cli.tui import run_tui

def init_handler(
    ctx: typer.Context,
    course_id: Optional[int],
    assignment_id: Optional[int],
    file: Optional[str],
    tui: bool = False,
):
    """Handle pulling assignment information from Canvas, optionally using TUI"""
    if tui:
        out = run_tui(file_select_enabled=True, file_select_escape_behavior="exit")
        
        if out is None:
            echo("Exiting...", ctx=ctx)
            raise typer.Abort()
        
        course, assignment, file_path = out
        course_id = course.get("id", None)
        assignment_id = assignment.get("id", None)
        file = file_path
    else:
        # Get the course_id, assignment_id, and file from the context or configs
        course_id = get_key("course_id", ctx)
        assignment_id = get_key("assignment_id", ctx)
        file = get_key("file", ctx)
    
    # Get attributes in npm style
    try:
        # Try to load the config file
        template_config = load_config(LOCAL_CONFIG_PATH)
    except FileNotFoundError:
        # If the file doesn't exist, create it
        template_config = {}
    
    
    message = """This utility will walk you through creating a canvas.json file.
It only covers the most common items, and tries to guess sensible defaults.

See `canvas help init` for definitive documentation on these fields (NOT IMPLEMENTED LOL)
and exactly what they do.

Use `canvas push --file <file>` to submit a specific file or just
`canvas push` to submit the default file.

Press ^C at any time to quit."""

    echo(message, ctx=ctx)
    
    # Make new config file
    config = template_config.copy()
    
    # Helper function to prompt for a value and set it in the config
    # with a default value of the old config if it exists
    def prompt_for_value_and_set(prompt, key, old_object, object, default=None):
        """Prompt for a value with a default and set it in the config"""
        if default is not None:
            prompt += f"({default}) "
        elif old_object and key in old_object:
            prompt += f"({old_object[key]}) "
        
        new_value = input(prompt).strip() or default or (old_object[key] if old_object and key in old_object else "")
        if new_value != "":
            object[key] = int(new_value) if key in ["course_id", "assignment_id"] else new_value
        return object
    
    try:
        # Get values from the user
        config = prompt_for_value_and_set("Course Name: ", "course_name", template_config, config)
        config = prompt_for_value_and_set("Course ID: ", "course_id", template_config, config, course_id)
        config = prompt_for_value_and_set("Assignment Name: ", "assignment_name", template_config, config)
        config = prompt_for_value_and_set("Assignment ID: ", "assignment_id", template_config, config, assignment_id)
        config = prompt_for_value_and_set("File: ", "file", template_config, config, file)
        
        # Show potential configuration to the user
        echo(f"About to write to {LOCAL_CONFIG_PATH}:\n", ctx=ctx)
        echo(json.dumps(config, indent=2), ctx=ctx)
        echo("\n", ctx=ctx)
        
        # Ask for confirmation before writing the file
        ok = input("Is this OK? (yes) ").strip().lower() or "yes"
        if ok != "yes" and ok != "y":
            echo("Aborted.", ctx=ctx)
            return
        
    except KeyboardInterrupt:
        # Handle Ctrl+C
        echo("\n\nExiting...", ctx=ctx)
        raise typer.Abort()
    
    # Save the config to the file
    try:
        save_config(LOCAL_CONFIG_PATH, config)
        echo(f"Configuration saved to {LOCAL_CONFIG_PATH}", ctx=ctx)
    except Exception as e:
        echo(f"Error saving configuration: {e}", ctx=ctx)
        raise typer.Abort()
    
    echo("\n", ctx=ctx)