"""
Args module for Canvas CLI
Contains argument parser configuration for the command-line interface
"""

import argparse
from typing import Callable, Dict
from .__version__ import __version__

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for Canvas CLI"""
    
    # Create the main parser
    parser = argparse.ArgumentParser(description="Canvas CLI tool")
    # Add version argument
    parser.add_argument('--version', action='version', version=f'canvas-cli (canvas-cmd) version {__version__}', help='Show version information')
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Config command
    setup_config_parser(subparsers)
    
    # Init command
    setup_init_parser(subparsers)
    
      # Push command
    setup_push_parser(subparsers)
    
    # Status command
    setup_status_parser(subparsers)

    # Pull command
    setup_pull_parser(subparsers)
    
    # Clone command
    setup_clone_parser(subparsers)

    return parser

def setup_config_parser(subparsers) -> None:
    """Set up the config command parser"""
    # Config command parser (matches git config style)
    config_parser = subparsers.add_parser("config", help="Configure Canvas API settings")
    
    # Helper function to accept --global or --local as mutually exclusive options
    def add_file_options_group(parser):
        group = parser.add_mutually_exclusive_group()
        # group.add_argument('--system', dest='scope', action='store_const', const='system', help='Use system config')
        group.add_argument('--global', dest='scope', action='store_const', const='global', help='Use global config')
        group.add_argument('--local', dest='scope', action='store_const', const='local', help='NI - Use local config')
        # group.add_argument('--worktree', dest='scope', action='store_const', const='worktree', help='Use worktree config')
        # group.add_argument('--file', dest='scope', metavar='FILE', help='Use given config file')

    # Helper function to add options to the parser
    def display_option_group(parser):
        parser.add_argument('--name-only', action='store_true', help='Show only the names/keys of the settings')
        parser.add_argument('--show-scope', action='store_true', help='NI - Show the scope of the settings (e.g. local, global)')
        parser.add_argument('--show-origin', action='store_true', help='NI - Show the origin of the settings (e.g. file:path)')
        return parser
    
    # Add subparsers for the config command
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Configuration subcommand")
    
    # 'list' subcommand
    list_parser = config_subparsers.add_parser("list", help="List all settings")
    add_file_options_group(list_parser)
    display_option_group(list_parser)
    # get_parser.add_argument('--includes', action='store_true')
    
    # 'get' subcommand
    get_parser = config_subparsers.add_parser("get", help="Get a setting value")
    add_file_options_group(get_parser)
    display_option_group(get_parser)
    # get_parser.add_argument('--includes', action='store_true')
    # get_parser.add_argument('--all', action='store_true', help='NI - Emits all values associated with key')
    # get_parser.add_argument('--regexp', action='store_true')
    # get_parser.add_argument('--value')
    # get_parser.add_argument('--fixed-value', action='store_true')
    # get_parser.add_argument('--default')
    get_parser.add_argument("name", help="Setting key to get")
    
    # 'set' subcommand
    set_parser = config_subparsers.add_parser("set", help="Set a setting value")
    add_file_options_group(set_parser)
    # set_parser.add_argument('--type', choices=['bool', 'int', 'bool-or-int', 'path', 'expiry'])
    # set_parser.add_argument('--all', action='store_true')
    # set_parser.add_argument('--value')
    # set_parser.add_argument('--fixed-value', action='store_true')
    set_parser.add_argument('name', help="Setting key to set")
    set_parser.add_argument('value', help="Value to set for the key")
    
    # 'unset' subcommand
    unset_parser = config_subparsers.add_parser("unset", help="Unset a setting value")
    add_file_options_group(unset_parser)
    # unset_parser.add_argument('--all', action='store_true')
    # unset_parser.add_argument('--value')
    # unset_parser.add_argument('--fixed-value', action='store_true')
    unset_parser.add_argument('name', help="Setting key to unset")

    # 'rename-section' subcommand
    # rename_section_parser = config_subparsers.add_parser("rename-section", help="Rename a section in the configuration")
    # add_file_options_group(rename_section_parser)
    # rename_section_parser.add_argument('old-name', help="Old section name")
    # rename_section_parser.add_argument('new-name', help="New section name")

    # 'remove-section' subcommand
    # remove_section_parser = config_subparsers.add_parser("remove-section", help="Remove a section from the configuration")
    # add_file_options_group(remove_section_parser)
    # remove_section_parser.add_argument('name', help="Section name to remove")

    # 'edit' subcommand
    edit_parser = config_subparsers.add_parser("edit", help="NI - Edit settings interactively")
    add_file_options_group(edit_parser)

    # Default command for implicit get/set not possible in argparse
    # config_parser.add_argument('name', nargs='?', help="Setting key")
    # config_parser.add_argument('value', nargs='?', help="Value to set for the key")

def setup_init_parser(subparsers) -> None:
    """Set up the init command parser"""
    init_parser = subparsers.add_parser("init", help="Initialize a Canvas project in the current directory")
    init_parser.add_argument("-cid", "--course_id", help="Course ID")
    init_parser.add_argument("-aid", "--assignment_id", help="Assignment ID")
    init_parser.add_argument("-cn", "--course_name", help="Course name")
    init_parser.add_argument("-an", "--assignment_name", help="Assignment name")
    init_parser.add_argument("-f", "--file", help="Path to the default file to submit")
    init_parser.add_argument("-t", "--tui", help="Select values from a User Interface", action="store_true")
    init_parser.add_argument("--fallback", dest="fallback_tui", help="Use fallback tui", action="store_true")

def setup_push_parser(subparsers) -> None:
    """Set up the push command parser"""
    push_parser = subparsers.add_parser("push", help="Submit an assignment to Canvas")
    push_parser.add_argument("-cid", "--course_id", metavar="id", type=int, help="Course ID")
    push_parser.add_argument("-aid", "--assignment_id", metavar="id", type=int, help="Assignment ID")
    push_parser.add_argument("-f", "--file", metavar="file", type=str, help="Path to the file to submit (optional if set during init)")

def setup_status_parser(subparsers) -> None:
    """Set up the status command parser"""
    status_parser = subparsers.add_parser("status", help="Get status about an assignment or class")
    status_parser.add_argument("-cid", "--course_id", metavar="id", type=int, help="Course ID")
    status_parser.add_argument("-aid", "--assignment_id", metavar="id", type=int, help="Assignment ID")
    
    status_parser.add_argument("-cd", "--course_details", action="store_true", help="Show course details")
    status_parser.add_argument("-a", "--all", action="store_true", help="Show all details including class information")
    status_parser.add_argument("-c", "--comments", action="store_true", help="NI - Show assignment comments")
    status_parser.add_argument("-g", "--grades", action="store_true", help="NI - Show assignment grades")
    
    status_parser.add_argument("-j", "--json", action="store_true", help="Output in JSON format")
    status_parser.add_argument("-t", "--tui", action="store_true", help="Use the TUI to select course and assignment")
    status_parser.add_argument("--fallback", dest="fallback_tui", help="Use fallback tui", action="store_true")
    subparser = status_parser.add_subparsers(dest="global_view", help="Show grades from all classes")
    global_parser = subparser.add_parser("all", help="Show grades from all classes")
    global_parser.add_argument("-m", "--messages", dest="messages", action="store_true", help="Show messages for global view")

def setup_pull_parser(subparsers) -> None:
    pull_parser = subparsers.add_parser("pull", help="Download assignment details from Canvas")    
    
    identify_group = pull_parser.add_argument_group("Course and Assignment Identification")
    identify_group.add_argument( "-cid", "--course_id", dest="course_id", metavar="COURSE_ID", type=int, help="Canvas Course ID (integer)." )
    identify_group.add_argument( "-aid", "--assignment_id", dest="assignment_id", metavar="ASSIGNMENT_ID", type=int, help="Canvas Assignment ID (integer)." )
    identify_group.add_argument("-t", "--tui", dest="tui", action="store_true", help="Use interactive Text-based User Interface to select course/assignment.")
    identify_group.add_argument("--fallback", dest="fallback_tui", action="store_true", help="Fallback to a basic TUI if the full interface is unavailable.")

    output_group = pull_parser.add_argument_group("Output Options")
    output_group.add_argument("-od", "--output-dir", dest="output_directory", type=str, default=".", help="Directory for submission")
    output_group.add_argument("-f", "--force", dest="overwrite_file", action="store_true", help="Overwrite existing files")

    download_group = pull_parser.add_argument_group("Download Options")
    download_group.add_argument("-dl", "--download-latest", dest="download_latest", action="store_true", help="Download the latest assignment submission")
    identify_group.add_argument("-dt", "--download-tui", dest="download_tui", action="store_true", help="Use interactive Text-based User Interface to select download.")

def setup_clone_parser(subparsers):
    clone_parser = subparsers.add_parser("clone", help="Download assignment details from Canvas")
    
    identify_group = clone_parser.add_argument_group("Course and Assignment Identification")
    identify_group.add_argument( "-cid", "--course_id", dest="course_id", metavar="COURSE_ID", type=int, help="Canvas Course ID (integer)." )
    identify_group.add_argument( "-aid", "--assignment_id", dest="assignment_id", metavar="ASSIGNMENT_ID", type=int, help="Canvas Assignment ID (integer)." )
    identify_group.add_argument("-t", "--tui", dest="tui", action="store_true", help="Use interactive Text-based User Interface to select course/assignment.")
    identify_group.add_argument("--fallback", dest="fallback_tui", action="store_true", help="Fallback to a basic TUI if the full interface is unavailable.")

    output_group = clone_parser.add_argument_group("Output Options")
    output_group.add_argument("-o", "--output", dest="output_file_destination", type=str, default="README.md", help="Filename for assignment output")
    output_group.add_argument("-od", "--output-dir", dest="output_directory", type=str, default="./canvas-page", help="Directory for crawled content")
#     output_group.add_argument("-os", "--stdout", dest="output_to_stdout", action="store_true", help="Output directly to terminal")
    output_group.add_argument("-ot", "--out-terminal", dest="display_in_terminal", action="store_true", help="Display output in terminal")
    output_group.add_argument("-f", "--force", dest="overwrite_file", action="store_true", help="Overwrite existing files")
    
    # Enforce logic: if --stdout or --out-terminal is set, --output must be provided to be passed
    def _enforce_output_logic(args, parser=clone_parser):
        # If --stdout is set, default output_file_destination to None
        if getattr(args, "output_to_stdout", False) or getattr(args, "display_in_terminal", False):
            args.output_file_destination = None
        elif not getattr(args, "output_file_destination", None):
            args.output_file_destination = "README.md"
    clone_parser.set_defaults(func=_enforce_output_logic)

    format_group = clone_parser.add_argument_group("Formatting Options")
#     format_group.add_argument("-fht", "--html", dest="keep_html_file", action="store_true", help="NI - Preserve HTML format")
    format_group.add_argument("-fmd", "--convert", dest="convert_to_markdown", action="store_true", help="NI - Convert all crawled content to Markdown (by default only markdown)")
    format_group.add_argument("-fi", "--integrate", dest="integrate_together", action="store_true", help="NI - Integrate crawled content into README")
    format_group.add_argument("-fl", "--convert-links", dest="convert_canvas_download_links", action="store_true", help="NI - Convert Canvas links to direct download")

    download_group = clone_parser.add_argument_group("Download Options")
    download_group.add_argument("-dpd", "--pdf", dest="download_pdfs", action="store_true", help="NI - Download PDF links")
    download_group.add_argument("-ddx", "--docx", dest="download_docx", action="store_true", help="NI - Download DOCX links")
    download_group.add_argument("-dc", "--pages", dest="crawl_canvas_pages", action="store_true", help="NI - Download linked Canvas pages")
#     download_group.add_argument("-da", "--download-all", dest="download_all_files", action="store_true", help="NI - Download all related files (e.g. images, zips)")
#     download_group.add_argument("-ds", "--download-submissions", dest="download_submissions", action="store_true", help="NI - Download all submissions")
    download_group.add_argument("-dd", "--delete-temp", dest="delete_after_convert", action="store_true", help="NI - Delete temporary files after processing")

def parse_args_and_dispatch(command_handlers: Dict[str, Callable]) -> None:
    """
    Parse command line arguments and dispatch to the appropriate handler
    
    Args:
        command_handlers: Dictionary mapping command names to handler functions
    """
    parser = create_parser()
    args = parser.parse_args()

    # Get the appropriate handler for the command
    command = args.command
    if command in command_handlers:
        command_handlers[command](args)
    else:
        parser.print_help()
