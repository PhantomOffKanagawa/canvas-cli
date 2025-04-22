"""
Helper functions for the CLI
"""

from .tui import run_tui, select_file
from .config import Config

def get_needed_args(args, required_args, verbose=False) -> list[str]:
    """
    Gets the value for the required arguments from the config file or TUI.

    Args:
        args: The arguments passed to the command.
        required_args: The required arguments for the command.
        verbose: Whether to print verbose output.
        
    Returns:
        still_missing: A list of arguments that are still missing after checking the config.
    """
    
    missing_args = [arg for arg in required_args if getattr(args, arg) is None]
    
    # Try to get the missing arguments from the config
    for arg in missing_args:
        args.__dict__[arg] = Config.get_value(arg, ["local", "global"])
    
    # Check if user requested the TUI interface
    if 'tui' in args and args.tui == True:
        # Run the TUI to select course and assignment
        course_id, assignment_id, course_name, assignment_name = run_tui(args.fallback_tui)
        
        # Check if course_id and assignment_id are provided
        # If not, raise an exception
        if not course_id or not assignment_id:
            raise Exception("Didn't select a course or assignment in TUI")
        
        # Update args with values from TUI
        args.course_id = course_id
        args.assignment_id = assignment_id
        args.course_name = course_name
        args.assignment_name = assignment_name
        
        if verbose:
            print(f"Selected course: {args.course_name} (ID: {args.course_id})")
            print(f"Selected assignment: {args.assignment_name} (ID: {args.assignment_id})")
            
        if 'file' in required_args:
            directory = args.output_directory if 'output_directory' in args else None
            file = select_file(directory, "Select a File", args.fallback_tui)
            
            if file is None:
                print("File selection cancelled.")
            else:
                if verbose:
                    print(f"Selected file: {file}")
                # Update args with the selected file
                args.file = file
            
    still_missing = [
        arg for arg in required_args if getattr(args, arg) is None
    ]
    
    return still_missing

def need_argument_output(command: str, missing_args: list[str]) -> None:
    """
    Prints the missing arguments for a command.

    Args:
        command: The command that is missing arguments.
        missing_args: The list of missing arguments.
    """
    
    # If missing any required arguments, show error and exit
    if missing_args:
        print(f"Error: Missing {', '.join(missing_args)}.")
        print("Please provide all requirements as arguments or set them in the local configuration.")
        print(f"Use 'canvas config list' to see the current configuration or 'canvas {command} -h' for help.")
        return