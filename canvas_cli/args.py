"""
Args module for Canvas CLI
Contains argument parser configuration for the command-line interface
"""

import argparse
from typing import Callable, Dict

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for Canvas CLI"""
      # Create the main parser
    parser = argparse.ArgumentParser(description="Canvas CLI tool")
    # Subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Config command
    setup_config_parser(subparsers)
    
    # Init command
    setup_init_parser(subparsers)
    
    # Push command
    setup_push_parser(subparsers)
    
    # Pull command
    setup_pull_parser(subparsers)
    
    # Status command
    setup_status_parser(subparsers)

    return parser

def setup_config_parser(subparsers: argparse.ArgumentParser) -> None:
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

def setup_init_parser(subparsers: argparse.ArgumentParser) -> None:
    """Set up the init command parser"""
    init_parser = subparsers.add_parser("init", help="Initialize a Canvas project in the current directory")
    init_parser.add_argument("-cid", "--course_id", help="Course ID")
    init_parser.add_argument("-aid", "--assignment_id", help="Assignment ID")
    init_parser.add_argument("-cn", "--course_name", help="Course name")
    init_parser.add_argument("-an", "--assignment_name", help="Assignment name")
    init_parser.add_argument("-f", "--file", help="Path to the default file to submit")
    init_parser.add_argument("-t", "--tui", help="Select values from a User Interface", action="store_true")
    init_parser.add_argument("--fallback", help="Use fallback tui", action="store_true")

def setup_init_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the `init` command to initialize a Canvas project in the current directory."""

    init = subparsers.add_parser(
        "init",
        help="Initialize a Canvas assignment folder with metadata and default settings."
    )

    # ───────────────────── Identification Options ─────────────────────
    identify = init.add_argument_group("Assignment Identification")
    identify.add_argument(
        "-cid", "--course_id",
        dest="course_id",
        metavar="COURSE_ID",
        type=int,
        help="Canvas Course ID (integer)."
    )
    identify.add_argument(
        "-aid", "--assignment_id",
        dest="assignment_id",
        metavar="ASSIGNMENT_ID",
        type=int,
        help="Canvas Assignment ID (integer)."
    )
    identify.add_argument(
        "-t", "--tui",
        dest="tui",
        action="store_true",
        help="Use interactive Text-based User Interface to select course/assignment."
    )
    identify.add_argument(
        "--fallback",
        dest="fallback_tui",
        action="store_true",
        help="Fallback to a basic TUI if the full interface is unavailable."
    )

    # ───────────────────── Naming Options ─────────────────────
    naming = init.add_argument_group("Naming and Metadata")
    naming.add_argument(
        "-cn", "--course-name",
        dest="course_name",
        metavar="COURSE_NAME",
        type=str,
        help="Readable name for the course (used in folder structure or metadata)."
    )
    naming.add_argument(
        "-an", "--assignment-name",
        dest="assignment_name",
        metavar="ASSIGNMENT_NAME",
        type=str,
        help="Readable name for the assignment."
    )

    # ───────────────────── File Setup Options ─────────────────────
    files = init.add_argument_group("File Configuration")
    files.add_argument(
        "-f", "--file",
        dest="default_file",
        metavar="FILE_PATH",
        type=str,
        help="Path to the default file to submit (e.g., main.py, report.pdf)."
    )

def setup_push_parser(subparsers: argparse.ArgumentParser) -> None:
    """Set up the push command parser"""
    push_parser = subparsers.add_parser("push", help="Submit an assignment to Canvas")
    push_parser.add_argument("-cid", "--course_id", metavar="id", type=int, help="Course ID")
    push_parser.add_argument("-aid", "--assignment_id", metavar="id", type=int, help="Assignment ID")
    push_parser.add_argument("-f", "--file", metavar="file", type=str, help="Path to the file to submit (optional if set during init)")

def setup_pull_parser(subparsers: argparse._SubParsersAction) -> None:
    """Set up the pull command parser with detailed and structured arguments."""

    pull_parser = subparsers.add_parser(
        "pull",
        help="Download assignment description and optionally crawl related files."
    )

    # ───────────────────────────── Assignment Identification ─────────────────────────────
    core_group = pull_parser.add_argument_group("Assignment Identification")
    core_group.add_argument(
        "-cid", "--course_id",
        dest="course_id",
        metavar="COURSE_ID",
        type=int,
        help="Canvas Course ID (integer)."
    )
    core_group.add_argument(
        "-aid", "--assignment_id",
        dest="assignment_id",
        metavar="ASSIGNMENT_ID",
        type=int,
        help="Canvas Assignment ID (integer)."
    )
    core_group.add_argument(
        "-t", "--tui",
        dest="tui",
        action="store_true",
        help="Use interactive Text-based User Interface to select course/assignment."
    )
    core_group.add_argument(
        "--fallback",
        dest="fallback_tui",
        action="store_true",
        help="Fallback to simplified TUI if main TUI fails."
    )

    # ───────────────────────────── Output Configuration ─────────────────────────────
    output_group = pull_parser.add_argument_group("Output Configuration")
    output_group.add_argument(
        "-o", "--output",
        dest="output_file",
        metavar="FILE",
        type=str,
        default="README.md",
        help="Filename for assignment description output (default: README.md)."
    )
    output_group.add_argument(
        "-od", "--output-directory",
        dest="output_dir",
        metavar="DIRECTORY",
        type=str,
        default="./canvas-page",
        help="Directory for saving crawled content (default: ./canvas-page)."
    )
    output_group.add_argument(
        "-f", "--force",
        dest="force_overwrite",
        action="store_true",
        help="Overwrite the output file if it already exists."
    )

    # ───────────────────────────── Description Formatting ─────────────────────────────
    format_group = pull_parser.add_argument_group("Formatting Options")
    format_group.add_argument(
        "-html",
        dest="keep_html",
        action="store_true",
        help="Preserve the assignment description as HTML instead of converting to Markdown."
    )
    format_group.add_argument(
        "-cnv", "--convert",
        dest="convert_to_md",
        action="store_true",
        help="Convert all crawled material into Markdown format."
    )
    format_group.add_argument(
        "-in", "--integrated",
        dest="integrate_into_readme",
        action="store_true",
        help="Integrate crawled material directly into the README.md output."
    )
    format_group.add_argument(
        "-de", "--delete_after",
        dest="delete_temp",
        action="store_true",
        help="Delete temporary crawl files after processing."
    )

    # ───────────────────────────── Download Behavior ─────────────────────────────
    download_group = pull_parser.add_argument_group("Download Options")
    download_group.add_argument(
        "-pdf",
        dest="download_pdfs",
        action="store_true",
        help="Download all PDF links found in the assignment description."
    )
    download_group.add_argument(
        "--pages",
        dest="download_pages",
        action="store_true",
        help="Download linked Canvas pages referenced in the description."
    )
    download_group.add_argument(
        "-dla", "--download_all",
        dest="download_all_files",
        action="store_true",
        help="NI - Download all assignment-related files into the specified output directory."
    )
    download_group.add_argument(
        "-cdl", "--convert_links",
        dest="convert_download_links",
        action="store_true",
        help="NI - Convert Canvas file links into direct download links."
    )

def setup_status_parser(subparsers: argparse._SubParsersAction) -> None:
    """Configure the `status` command for viewing assignment or course status."""

    status = subparsers.add_parser(
        "status",
        help="Get status details about an assignment, course, or all classes."
    )

    # ───────────────────── Identification Options ─────────────────────
    identify = status.add_argument_group("Assignment Identification")
    identify.add_argument(
        "-cid", "--course_id",
        dest="course_id",
        metavar="COURSE_ID",
        type=int,
        help="Canvas Course ID (integer)."
    )
    identify.add_argument(
        "-aid", "--assignment_id",
        dest="assignment_id",
        metavar="ASSIGNMENT_ID",
        type=int,
        help="Canvas Assignment ID (integer)."
    )
    identify.add_argument(
        "-t", "--tui",
        dest="tui",
        action="store_true",
        help="Use interactive Text-based User Interface to select course/assignment."
    )
    identify.add_argument(
        "--fallback",
        dest="fallback_tui",
        action="store_true",
        help="Fallback to simplified TUI if main TUI fails."
    )

    # ───────────────────── Detail Options ─────────────────────
    details = status.add_argument_group("Information Detail")
    details.add_argument(
        "-cd", "--course-details",
        dest="show_course_details",
        action="store_true",
        help="Show basic course metadata."
    )
    details.add_argument(
        "-a", "--all",
        dest="show_all_details",
        action="store_true",
        help="Show all details including class-level metadata."
    )
    details.add_argument(
        "-c", "--comments",
        dest="show_comments",
        action="store_true",
        help="(Not Implemented) Show comments on the assignment."
    )
    details.add_argument(
        "-g", "--grades",
        dest="show_grades",
        action="store_true",
        help="(Not Implemented) Show grades for the assignment."
    )

    # ───────────────────── Output Options ─────────────────────
    output = status.add_argument_group("Output Formatting")
    output.add_argument(
        "-j", "--json",
        dest="output_json",
        action="store_true",
        help="Display the result in JSON format."
    )

    # ───────────────────── Global View Subcommand ─────────────────────
    global_view_subparsers = status.add_subparsers(
        dest="global_view",
        metavar="VIEW",
        help="Optional subcommand to show status across all classes."
    )

    global_parser = global_view_subparsers.add_parser(
        "all",
        help="Show summary from all enrolled courses."
    )
    global_parser.add_argument(
        "-m", "--messages",
        dest="show_messages",
        action="store_true",
        help="Show messages alongside global status view."
    )
    global_parser.add_argument(
        "-j", "--json",
        dest="output_json",
        action="store_true",
        help="Display the result in JSON format."
    )


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
