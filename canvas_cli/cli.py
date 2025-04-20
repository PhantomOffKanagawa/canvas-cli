"""
CLI Manager Module for Canvas CLI Tool
Handles command line interface for Canvas CLI tool and its subcommands.
"""

import json
from pathlib import Path
import sys
import os
import pydoc

from .config import Config
from .api import CanvasAPI, format_date
from .args import parse_args_and_dispatch
from .tui import run_tui
from .status_helpers import show_global_status, show_local_status

def config_command(args):
    """Handle command line arguments for configuration"""
    if args is None:
        args = type('Args', (), {})()

    # Check if there is no subcommand
    if args.config_command == None:
        print("error: no action specified")
        print("See 'canvas config --help' for available actions")
        return
    
    # Default scope to 'global' if not provided
    # TODO: Cascade the scope from local to global if not provided
    args.scope = "global" if args.scope is None else args.scope

    if args.config_command == "list":
        # Handle list command
        try:
            # List all settings from respective configuration
            if args.scope == "global":
                config = Config.load_global()
                if config is None:
                    print("No global configuration found.")
                    return
                for key, value in config.items():
                    print(f"{key}{'' if args.name_only else ': ' + value}")
            elif args.scope == "local":
                config = Config.load_project_config()
                if config is None:
                    print("No local configuration found.")
                    return
                for key, value in config.items():
                    print(f"{key}{'' if args.name_only else ': ' + value}")
        except Exception as e:
            print(f"Error: {e}")
        return
    elif args.config_command == "get":
        # Handle get command
        try:
            value = Config.get_value(args.name, args.scope)
            if value is not None:
                print(f"{args.name}{'' if args.name_only else ': ' + value}")
            else:
                print(f"Key '{args.name}' not found in {args.scope} configuration.")
        except Exception as e:
            print(f"Error: {e}")
        return
    elif args.config_command == "set":
        # Handle set command
        try:
            Config.set_value(args.name, args.value, args.scope)
            print(f"Set {args.name} to {args.value} in {args.scope} configuration.")
        except Exception as e:
            print(f"Error: {e}")
        return
    elif args.config_command == "unset":
        # Handle unset command
        try:
            if Config.unset_value(args.name, args.scope):
                print(f"Unset {args.name} from {args.scope} configuration.")
            else:
                print(f"Key '{args.name}' not found in {args.scope} configuration.")
        except Exception as e:
            print(f"Error: {e}")

def init_command(args):
    """Handle the init command to create a local .canvas-cli directory"""
    """Inspired by npm init"""

    # Check if user requested the TUI interface
    if args.tui:
        # Run the TUI to select course and assignment
        course_id, assignment_id, course_name, assignment_name = run_tui(args.fallback)
        
        # Check if course_id and assignment_id are provided
        # If not, exit the function
        if not course_id or not assignment_id:
            return
        
        # Update args with values from TUI
        args.course_id = course_id
        args.assignment_id = assignment_id
        args.course_name = course_name
        args.assignment_name = assignment_name
        
        print(f"Selected: {course_name} (ID: {course_id})")
        print(f"Assignment: {assignment_name} (ID: {assignment_id})")
        
    # Check if the current directory is a valid project directory
    # If so, use existing values as defaults
    try:
        old_config = Config.load_project_config()
    except Exception as e:
        print(f"Error loading local configuration: {e}")
        old_config = {}
        return

    message = """This utility will walk you through creating a canvas.json file.
It only covers the most common items, and tries to guess sensible defaults.

See `canvas help init` for definitive documentation on these fields (NOT IMPLEMENTED LOL)
and exactly what they do.

Use `canvas push --file <file>` to submit a specific file or just
`canvas push` to submit the default file.

Press ^C at any time to quit."""

    print(message)

    # Make config
    config = old_config

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
            object[key] = new_value
        return object
    
    try:
        # Get values from the user
        prompt_for_value_and_set("assignment name: ", "assignment_name", old_config, config, args.assignment_name)
        prompt_for_value_and_set("course name: ", "course_name", old_config, config, args.course_name)
        prompt_for_value_and_set("assignment id: ", "assignment_id", old_config, config, args.assignment_id)
        prompt_for_value_and_set("course id: ", "course_id", old_config, config, args.course_id)
        prompt_for_value_and_set("default submission file: ", "default_upload", old_config, config, args.file)

        # Get the current working directory from the command line
        config_dir = Path.cwd()

        # Show potential configuration to the user
        print(f"About to write to {config_dir}\\canvas.json:\n")
        print(json.dumps(config, indent=2))
        print()

        # Ask for confirmation before writing the file
        ok = input("Is this OK? (yes) ").strip().lower() or "yes"
        if ok != "yes" and ok != "y":
            print("Aborted.")
            return
    except KeyboardInterrupt:
        print("\nAborted by user (Ctrl+C).")
        return
    
    # Save the local configuration
    try:
        Config.save_project_config(config, config_dir)
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return
    
    print()

def push_command(args):
    """Handle the push command to submit assignments"""
    # If course_id and assignment_id are not provided, try to load from local config
    course_id = args.course_id
    assignment_id = args.assignment_id
    file_path = args.file
    
    # Check if course_id and assignment_id are provided
    if not course_id or not assignment_id:
        # If not load from local_config
        local_config = Config.load_project_config()

        if local_config:
            if not course_id:
                course_id = local_config.get("course_id")
            
            if not assignment_id:
                assignment_id = local_config.get("assignment_id")

    # If file is not provided, try to get from local config
    if not file_path:
        local_config = Config.load_project_config()
        if local_config and "default_upload" in local_config:
            file_path = local_config.get("default_upload")

    # If missing any required arguments, show error and exit
    if not course_id or not assignment_id or not file_path:
        missing = []
        if not course_id:
            missing.append('course_id')
        if not assignment_id:
            missing.append('assignment_id')
        if not file_path:
            missing.append('file_path')
        print(f"Error: Missing {', '.join(missing)}.")
        print("Please provide all requirements as arguments or set them in the local configuration.")
        print("Use 'canvas config list' to see the current configuration or 'canvas push -h' for help.")
        return
    
    # Ensure the file path is absolute
    file_path = Path(file_path).resolve()

    # Ensure we have permission to read the file
    try:
        with open(file_path, 'rb') as f:
            pass  # Just check if we can read the file
    except PermissionError:
        # Handle permission error
        print(f"Error: Permission denied to read file '{file_path}'.")
        return
    except FileNotFoundError:
        # Handle file not found error
        print(f"Error: File '{file_path}' not found.")
        return
    finally:
        # Close the file if it was opened
        if 'f' in locals():
            f.close()

    # Create API client and submit the assignment
    try:
        api = CanvasAPI()
        api.submit_assignment(course_id, assignment_id, file_path)
    except ValueError as e:
        print(f"Error: {e}")
        return

def status_command(args):
    """Handle the status command to get assignment and course information"""
    # Initialize API client
    try:
        api = CanvasAPI()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Check if global view is requested
    if args.global_view:
        show_global_status(api, args)
        return

    # Determine if we should use TUI to select course/assignment
    if args.tui:
        # Run the TUI to select course and assignment
        course_id, assignment_id, course_name, assignment_name = run_tui(fallback=args.fallback)
        
        if not course_id or not assignment_id:
            print("Status check cancelled.")
            return
        
        # Update args with values from TUI
        args.course_id = course_id
        args.assignment_id = assignment_id
    
    # Get course_id and assignment_id from args or config
    course_id = args.course_id
    assignment_id = args.assignment_id
    
    # If not provided, try to get from local config
    if not course_id or not assignment_id:
        local_config = Config.load_project_config()
        if local_config:
            if not course_id:
                course_id = local_config.get("course_id")
            if not assignment_id:
                assignment_id = local_config.get("assignment_id")
    
    # If still missing required arguments, show error and exit
    if not course_id:
        print("Error: Missing course_id.")
        print("Please provide a course ID with --course_id or select one using --tui.")
        return
    
    show_local_status(args, api, course_id, assignment_id)

def help_command(args):
    """Handle the help command to show help information"""
    if args.help_command:
        # Show help for a specific command
        print(f"Help for command '{args.help_command}':")
        # Use pydoc to show help
        # pydoc.pager(pydoc.render_doc(args.help_command))
    else:
        print("Available commands:")
        print("  config  - Configure Canvas API settings")
        print("  init    - Initialize a Canvas project")
        print("  push    - Submit an assignment to Canvas")
        print("  status  - Get status information about assignments and courses")
        print("  help    - Show help information")

def main():
    """Main CLI entry point"""
    # Define command handlers
    command_handlers = {
        "config": config_command,
        "init": init_command,
        "push": push_command,
        "status": status_command,
        "help": help_command
    }
    
    # Parse arguments and dispatch to the appropriate handler
    parse_args_and_dispatch(command_handlers)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, show help
        from .args import create_parser
        parser = create_parser()
        parser.print_help()
        print("\nNI - Not Implemented Yet")
    else:
        main()
