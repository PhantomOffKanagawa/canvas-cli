"""
CLI Manager Module for Canvas CLI Tool
Handles command line interface for Canvas CLI tool and its subcommands.
"""

import json
from pathlib import Path
import sys
import os
import re

from canvas_cli.cli_utils import get_needed_args, need_argument_output
from .__version__ import __version__

from .config import Config
from .api import CanvasAPI, download_file, format_date, submit_assignment
from .args import parse_args_and_dispatch
from .tui import run_tui, select_file, select_from_options
from .command_status import show_global_status, show_local_status
from .command_clone import handle_clone_command, validate_clone_args

def config_command(args):
    """Handle command line arguments for configuration"""
        
    # Check if there is no subcommand
    if args.config_command == None:
        print("Error: no action specified")
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
                    print(f"{key}{'' if args.name_only else ': ' + str((value))}")
            elif args.scope == "local":
                config = Config.load_project_config()
                if config is None:
                    print("No local configuration found.")
                    return
                for key, value in config.items():
                    print(f"{key}{'' if args.name_only else ': ' + str((value))}")
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

    try:
        missing_args = get_needed_args(args, ["course_id", "assignment_id", "course_name", "assignment_name", "file"], True)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # If file set and can be relative, make it relative to the current directory
    if 'file' in args and args.file is not None:
        file_path = Path(args.file).resolve()
        try:
            args.file = os.path.join('./', file_path.relative_to(Path.cwd()))
        except ValueError:
            args.file = file_path
        
    # Check if the current directory is a valid project directory
    # If so, use existing values as defaults
    try:
        old_config = Config.load_project_config()
    except Exception as e:
        print(f"Error loading local configuration: {e}")
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
    config = old_config.copy() if old_config else {}

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
    
def pull_command(args):
    """Handle the pull command to download submissions"""
    # Try to get the course_id and assignment_id from the config
    try:
        missing_args = get_needed_args(args, ["course_id", "assignment_id"], True)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    if missing_args:
        need_argument_output("pull", missing_args)
        return
    
    # Determine Course and Assignment IDs
    course_id = args.course_id
    assignment_id = args.assignment_id
    
    # Determine what we need to clone using download-group
    download_latest: bool = args.download_latest
    
    # Determine how output will be handled using output-group
    output_directory: str = str(Path.cwd().joinpath(Path(args.output_directory)).resolve())
    overwrite: bool = args.overwrite_file
    tui = args.tui
    tui_for_download = args.download_tui
    fallback_tui = args.fallback_tui
    
    # Get API client
    try:
        api = CanvasAPI()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Get the submissions response json
    submissions_resp = api.get_submissions(course_id, assignment_id)
    if not submissions_resp:
        print(f"No submissions found for assignment {assignment_id} in course {course_id}.")
        return
    
    # Get the submissions from the response
    submissions = submissions_resp.get("submission_history", None)
    
    # If there are no submissions, show an error message
    if not submissions or len(submissions) == 0:
        print(f"No submissions found for assignment {assignment_id} in course {course_id}.")
        return
    # If there is only one submission or the user wants to download the latest, download it
    elif len(submissions) == 1 or download_latest:
        # Get the latest submission
        print(f"Found {len(submissions)} submission for assignment {assignment_id} in course {course_id}.")
        
        # Get attachments from the latest submission
        attachments = submissions[len(submissions) - 1].get("attachments", None)
        
        # Download the attachments if they exist
        for attach in attachments:
            download_file(attach.get("url", None), os.path.join(output_directory, attach.get("filename", None)), overwrite=overwrite)
        print(f"Downloaded {len(attachments)} attachments from the latest submission to {output_directory}.")
        return
            
    else:
        # If there are multiple submissions, show a list to the user and let them select one
        print(f"Found {len(submissions)} submissions for assignment {assignment_id} in course {course_id}.")
        # Inject Labels into the submissions for display
        points_possible = submissions_resp.get("assignment", {}).get("points_possible", None)
        for i, submission in enumerate(submissions):
            submitted_at = submission.get("submitted_at", None)
            submission_type = submission.get("submission_type", None)
            score = submission.get("score", None) or submission.get("points", None)
            display_name = ", ".join([attach.get("display_name", None) for attach in submission.get("attachments", None)])
            submissions[i]["meta_label"] = f"Submission {i+1}{' - ' + format_date(submitted_at) if submitted_at else ''}{' - ' + submission_type if submission_type else ''}{' - ' + score + '/' + points_possible if score and points_possible else ''}{' - ' + display_name if display_name else ' - No Display Name'}"
        
        use_fallback = fallback_tui or not (tui_for_download or tui)
        selected_submission = select_from_options(submissions, "meta_label", "Select a submission to download:", fallback=use_fallback)
        
        if selected_submission is None:
            print("No submission selected.")
            return
        
        attachments = selected_submission.get("attachments", None)
        if attachments:
            for attach in attachments:
                download_file(attach.get("url", None), os.path.join(output_directory, attach.get("filename", None)), overwrite=overwrite)
            print(f"Downloaded {len(attachments)} attachments from the latest submission to {output_directory}.")
        return

def clone_command(args):
    """Handle the clone command to download assignments"""
    # Validate and get required arguments
    if not validate_clone_args(args):
        return
    
    handle_clone_command(args)

def push_command(args):
    """Handle the push command to submit assignments"""
    # Get args
    try:
        missing_args = get_needed_args(args, ["course_id", "assignment_id", "file"], True)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    if missing_args:
        need_argument_output("push", missing_args)
        return
    
    course_id = args.course_id
    assignment_id = args.assignment_id
    file_path = args.file

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

    # Create API client and submit the assignment
    try:
        api = CanvasAPI()
        submit_assignment(course_id, assignment_id, file_path)
    except ValueError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        print(f"Traceback: {e.__traceback__}")
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
    
    try:
        get_needed_args(args, ["course_id", "assignment_id"], True)
    except Exception as e:
        print(f"Error: {e}")
        return
    
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
        print("  pull    - Download assignment submissions from Canvas")
        print("  clone   - Download assignment details from Canvas")
        print("  status  - Get status information about assignments and courses")
        print("  help    - Show help information")

def main():
    """Main CLI entry point"""
    # Define command handlers
    command_handlers = {
        "config": config_command,
        "init": init_command,
        "pull": pull_command,
        "clone": clone_command,
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
