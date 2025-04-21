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
from .api import CanvasAPI, download_file, format_date
from .args import parse_args_and_dispatch
from .tui import run_tui, select_file, select_from_options
from .command_status import show_global_status, show_local_status

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

    try:
        get_needed_args(args, ["course_id", "assignment_id", "course_name", "assignment_name", "file"], True)
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
    output_directory: str = Path.cwd().joinpath(Path(args.output_directory)).resolve()
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
        print(f"Downloaded {len(attachments)} attachments to {output_directory}.")
        return
    
    
def clone_command(args):
    """Handle the clone command to download assignments"""
    # Try to get the course_id and assignment_id from the config
    try:
        missing_args = get_needed_args(args, ["course_id", "assignment_id"], True)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    if missing_args:
        need_argument_output("clone", missing_args)
        return
    
    # Determine Course and Assignment IDs
    course_id = args.course_id
    assignment_id = args.assignment_id
    
    # Determine what we need to clone using download-group
    download_pdfs: bool = args.download_pdfs
    download_docx: bool = args.download_docx
    crawl_canvas_pages: bool = args.crawl_canvas_pages
    # download_all_files: bool = args.download_all_files
    # download_submissions: bool = args.download_submissions
    delete_after_convert: bool = args.delete_after_convert
    
    # Determine formatting actions using format-group
    # keep_html_file: bool = args.keep_html_file
    convert_to_markdown: bool = args.convert_to_markdown
    integrate_together: bool = args.integrate_together
    convert_links: bool = args.convert_canvas_download_links
    
    # Determine output options using output-group
    output_file_destination: str = args.output_file_destination
    output_directory: str = args.output_directory
    # output_to_stdout: bool = args.output_to_stdout
    display_in_terminal: bool = args.display_in_terminal
    overwrite: bool = args.overwrite_file
    
    # Calculated attributes
    do_save_main_file: bool = output_file_destination is not None
    will_have_temp_files: bool = ((download_pdfs or crawl_canvas_pages) and convert_to_markdown)
    use_temp_dir: bool = delete_after_convert and will_have_temp_files
    download_dir: str = os.path.join(os.getcwd(), output_directory, ".canvas.temp") if use_temp_dir else os.path.join(os.getcwd(), output_directory)
    
    try:
        if will_have_temp_files:
            # Create the download directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating download directory: {e}")
        return
        
    
    # Initialize API client
    try:
        api = CanvasAPI()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Get the assignment details
    try:
        assignment = api.get_assignment_details(course_id, assignment_id)
        if not assignment:
            print(f"Assignment with ID {assignment_id} not found in course {course_id}.")
            return
    except Exception as e:
        print(f"Error fetching assignment details: {e}")
        return
    
    html: dict = {}
    
    description = assignment.get("description", None)
    if description is None:
        print(f"No description found for assignment {assignment_id} in course {course_id}.")
        return
    
    html['description'] = description
    
    # Hold all fetched files to avoid duplicates
    fetched = set()
    
    # If crawl pages is enabled, fetch all canvas pages in the description recursively
    if crawl_canvas_pages:
        process_pages = list(html.values())
        # Find all canvas pages in the HTML content
        def find_pages(content):
            """Find all canvas pages in the HTML content"""
            try:
                from .config import Config
                canvas_url = Config.get_value("host", ["local", "global"])
                if canvas_url is None:
                    print("Error: canvas_url not set in configuration.")
                    return
                
                # Regular expression to match Canvas page links
                # <a title="M13 Assignment Tasks" href="https://umsystem.instructure.com/courses/296958/pages/m13-assignment-tasks" data-api-endpoint="https://umsystem.instructure.com/api/v1/courses/296958/pages/m13-assignment-tasks" data-api-returntype="Page">M13 Assignment Tasks</a>
                page_links = re.findall(
                    r'<a [^>]*href="(https?:\/\/' + canvas_url.replace(".", "\.") + r'\/courses\/\d+\/pages\/[^"]+)"[^>]*data-api-endpoint="([^"]+)"[^>]*data-api-returntype="Page"[^>]*>([^<]+)<\/a>',
                    content,
                    re.IGNORECASE,
                )
                
                if page_links:
                    for href, api_endpoint, title in page_links:
                        if href in fetched:
                            print(f"Already fetched page link: {href}")
                            continue
                        
                        print(f"Found page link: {href}")
                        response = api.get_canvas_page(api_endpoint)
                        if response and 'body' in response:
                            page_content = response['body']
                            fetched.add(href)
                            html[title] = page_content
                            process_pages.append(page_content)
            except Exception as e:
                print(f"Error: {e}")
                
        while process_pages:
            page = process_pages.pop(0)
            find_pages(page)
    
    # Search for all Canvas links in the HTML content
    # Replace download links with the actual download link
    # Add warning for canvas pages that are not downloadable
    if convert_links:
        for title, content in html.items():
            try:
                from .config import Config
                canvas_url = Config.get_value("host", ["local", "global"])
                if canvas_url is None:
                    print("Error: canvas_url not set in configuration.")
                    return
                
                # Regular expression to match Canvas page links
                # <a title="M13 Assignment Tasks" href="https://umsystem.instructure.com/courses/296958/pages/m13-assignment-tasks" data-api-endpoint="https://umsystem.instructure.com/api/v1/courses/296958/pages/m13-assignment-tasks" data-api-returntype="Page">M13 Assignment Tasks</a>
                # Replace the text of Canvas page links with "(Canvas Link)" appended
                def add_canvas_link_label(match):
                    return match.group(0).replace(match.group(2), f"{match.group(2)} (Canvas Link)")

                content = re.sub(
                    r'(<a [^>]*href="https?:\/\/' + canvas_url.replace(".", r"\.") + r'\/[^"]+"[^>]*data-api-endpoint="[^"]+"[^>]*data-api-returntype="Page"[^>]*>)([^<]+)(<\/a>)',
                    add_canvas_link_label,
                    content,
                    flags=re.IGNORECASE,
                )
                
                # Replace Canvas file links with a second copy of the link using the download URL
                def add_download_link(match):
                    href = match.group(1)
                    title = match.group(2)
                    # Match the expected Canvas file URL pattern
                    file_match = re.match(
                        r"(https:\/\/" + canvas_url.replace(".", r"\.") + r"\/courses\/\d+\/files\/\d+)\?verifier=([A-Za-z0-9]+)&amp;wrap=1",
                        href,
                    )
                    if file_match:
                        base_url, verifier = file_match.groups()
                        download_url = f"{base_url}/download?download_frd=1&verifier={verifier}"
                        # Return the original link plus a new download link
                        return f'<a href="{href}">{title}</a> <a href="{download_url}">(Download)</a>'
                    else:
                        return match.group(0)

                content = re.sub(
                    r'<a[^>]+href="([^"]+)"[^>]*>([^<]+\.(?:pdf|docx?s?))</a>',
                    add_download_link,
                    content,
                    flags=re.IGNORECASE,
                )
                
                html[title] = content
                
            except Exception as e:
                print(f"Error: {e}")
                return
            
        
    pdfs = []
    if download_pdfs:
        # Find all Canvas PDF links in the HTML content
        pdf_links = {}
        try:
            from .config import Config
            canvas_url = Config.get_value("host", ["local", "global"])
            if canvas_url is None:
                print("Error: canvas_url not set in configuration.")
                return
                
            for page in html.values():
                false_links = (re.findall(
                    r'<a[^>]+href="([^"]+)"[^>]*>([^<]+\.pdf)</a>',
                    page,
                    re.IGNORECASE,
                ))
                for href, title in false_links:
                    # Only match links with the expected pattern
                    match = re.match(
                        r"(https:\/\/" + canvas_url.replace(".", "\.") + r"\/courses\/\d+\/files\/\d+)\?verifier=([A-Za-z0-9]+)&amp;wrap=1",
                        href,
                    )
                    if match:
                        base_url, verifier = match.groups()
                        # Construct the full URL
                        download_url = f"{base_url}/download?download_frd=1&verifier={verifier}"
                        pdf_links[title] = download_url
        except Exception as e:
            print(f"Error: {e}")
            return        
        
        try:
            if pdf_links:
                for title, href in pdf_links.items():
                    if href in fetched:
                        print(f"Already fetched PDF link: {href}")
                        continue
                    
                    print(f"Found PDF link: {href}")
                    filename = os.path.join(download_dir, title)
                    response = download_file(href, filename, overwrite=overwrite)
                    if response:
                        fetched.add(href)
                        pdfs.append(filename)
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            
    docs = []
    if download_docx:
        # Find all Canvas DOCX links in the HTML content
        doc_links = {}
        try:
            import re
            from .config import Config
            canvas_url = Config.get_value("host", ["local", "global"])
            if canvas_url is None:
                print("Error: canvas_url not set in configuration.")
                return
                
            for page in html.values():
                false_links = (re.findall(
                    r'<a[^>]+href="([^"]+)"[^>]*>([^<]+\.docx?s?)</a>',
                    page,
                    re.IGNORECASE,
                ))
                for href, title in false_links:
                    # Only match links with the expected pattern
                    match = re.match(
                        r"(https:\/\/" + canvas_url.replace(".", "\.") + r"\/courses\/\d+\/files\/\d+)\?verifier=([A-Za-z0-9]+)&amp;wrap=1",
                        href,
                    )
                    if match:
                        base_url, verifier = match.groups()
                        # Construct the full URL
                        download_url = f"{base_url}/download?download_frd=1&verifier={verifier}"
                        doc_links[title] = download_url
        except Exception as e:
            print(f"Error: {e}")
            return
        
        try:
            if doc_links:
                for title, href in doc_links.items():
                    if href in fetched:
                        print(f"Already fetched DOCX link: {href}")
                        continue
                    
                    print(f"Found DOCX link: {href}")
                    filename = os.path.join(download_dir, title)
                    response = download_file(href, filename, overwrite=overwrite)
                    if response:
                        fetched.add(href)
                        docs.append(filename)
        except Exception as e:
            print(f"Error downloading DOCX: {e}")
            
    markdown = {}
    readme = ""
    if convert_to_markdown:
        if html and len(html.values()) != 0:  # Fixed method call to values()
            try:
                from markitdown import MarkItDown
                import io
                md = MarkItDown(enable_plugins=True) # Set to True to enable plugins
                for title, content in html.items():
                    # Convert HTML string to Markdown
                    if isinstance(content, str):
                        content_stream = io.BytesIO(content.encode("utf-8"))
                    else:
                        content_stream = content
                    result = md.convert_stream(content_stream)
                    markdown_content = result.text_content
                        
                    if title == "description":
                        text = markdown_content
                        readme = text
                    else:
                        text = "#" + title + "\n" + markdown_content
                        markdown[title] = text
                
            except ImportError:
                import importlib.metadata
                command_name = importlib.metadata.name("canvas-cmd")
                print(f"Error: markitdown module not found. Cannot convert to markdown.\n Run 'pip install {command_name}[convert]' to install the required dependencies for converting.")
                return
            
        if pdfs and len(pdfs) != 0:
            try:
                from markitdown import MarkItDown
                md = MarkItDown(enable_plugins=True) # Set to True to enable plugins
                for pdf in pdfs:
                    # Convert the PDF to Markdown
                    pdf_path = Path(pdf)
                    # Ensure its a pdf file
                    if pdf_path.suffix.lower() != ".pdf":
                        print(f"Skipping non-PDF file: {pdf_path}")
                        continue
                    result = md.convert(pdf_path)
                    text = "#" + pdf + "\n" + result.text_content
                    markdown[pdf] = text
            except ImportError:
                import importlib.metadata
                command_name = importlib.metadata.name("canvas-cmd")
                print(f"Error: markitdown module not found. Cannot convert to markdown.\n Run 'pip install {command_name}[convert]' to install the required dependencies for converting.")
                return
            
        if docs and len(docs) != 0:
            try:
                from markitdown import MarkItDown
                md = MarkItDown(enable_plugins=True) # Set to True to enable plugins
                for doc in docs:
                    # Convert the DOCX to Markdown
                    doc_path = Path(doc)
                    # Ensure its a docx file
                    if doc_path.suffix.lower() != ".docx":
                        print(f"Skipping non-DOCX file: {doc_path}")
                        continue
                    result = md.convert(doc_path)
                    text = "#" + doc + "\n" + result.text_content
                    markdown[doc] = text
            except ImportError:
                import importlib.metadata
                command_name = importlib.metadata.name("canvas-cmd")
                print(f"Error: markitdown module not found. Cannot convert to markdown.\n Run 'pip install {command_name}[convert]' to install the required dependencies for converting.")
                return
            
    else:
        # If not converting to markdown, just save the HTML content
        readme = html.get("description", None)
        if readme is None:
            print(f"No description found for assignment {assignment_id} in course {course_id}.")
            return
            
    if delete_after_convert:
        # Delete the temporary files after download
        try:
            for file in os.listdir(download_dir):
                file_path = os.path.join(download_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(download_dir)
            print(f"Deleted temporary files in {download_dir}.")
        except Exception as e:
            print(f"Error deleting temporary files: {e}")
            return
        
    if integrate_together:
        # Integrate all markdown files into one
        for key, value in markdown.items():
            if key == "description":
                continue
            readme = readme + "\n\n# " + key + "\n" + value
        markdown = {}
        
    if do_save_main_file:
        # Save the markdown to a file
        try:
            
            if readme != "":
                # Save the readme to a file
                # Ensure the output file path is absolute
                output_file_destination = Path(output_file_destination).resolve()
                # Create the directory if it doesn't exist
                os.makedirs(output_file_destination.parent, exist_ok=True)
                # Save the readme to a file
                with open(output_file_destination, "w", encoding="utf-8") as f:
                    f.write(readme)
                print(f"Saved markdown to {output_file_destination}.")
                    
            if markdown and len(markdown) != 0:
                # Save the markdown to a file
                # Ensure the output file path is absolute
                output_file_destination = Path(output_directory).resolve()
                # Create the directory if it doesn't exist
                os.makedirs(output_file_destination, exist_ok=True)
                # Save the markdown to a file
                for name, text in markdown.items():
                    # Create a new file for each markdown file
                    output_file_destination = os.path.join(output_directory, f"assignment_{assignment_id}_{name}.md")
                    with open(output_file_destination, "w", encoding="utf-8") as f:
                        f.write(text)
                print(f"Saved markdown to {output_directory}.")
            
        except Exception as e:
            print(f"Error saving markdown: {e}")
            return
        
    if display_in_terminal:
        try:
            from rich.console import Console
            from rich.markdown import Markdown
            console = Console()
            console.print(Markdown(readme))
        except ImportError:
            import importlib.metadata
            command_name = importlib.metadata.name("canvas-cmd")
            print(f"Error: markitdown module not found. Cannot convert to markdown.\n Run 'pip install {command_name}[gui]' to install the required dependencies for converting.")
            return

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
