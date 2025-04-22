"""
Helper functions for the Canvas CLI clone command
Handles downloading and converting assignments and files from Canvas.
"""

import json
from pathlib import Path
import sys
import os
import re

from canvas_cli.api import CanvasAPI, download_file
from canvas_cli.cli_utils import get_needed_args, need_argument_output

def handle_clone_command(args) -> None:
    """Main function to handle the clone command"""
    
    # Extract parameters and prepare environment
    params = _prepare_clone_parameters(args)
    
    # Initialize API client
    api = _get_api_client()
    if not api:
        return
    
    # Get assignment details
    assignment = _get_assignment_details(api, args.course_id, args.assignment_id)
    if not assignment:
        return
    
    # Process HTML content
    html_content = _process_html_content(api, assignment, params)
    
    # Download files if requested
    pdfs = _download_files(html_content, params, file_type='pdf') if params['download_pdfs'] else []
    docs = _download_files(html_content, params, file_type='docx') if params['download_docx'] else []
    
    # Convert content to markdown if requested
    markdown_content = _convert_to_markdown(html_content, pdfs, docs, params)
    
    # Clean up temporary files if needed
    if params['delete_after_convert']:
        _cleanup_temp_files(params['download_dir'])
    
    # Save and display output
    _save_output(markdown_content, params)
    
    # Display in terminal if requested
    if params['display_in_terminal']:
        _display_in_terminal(markdown_content.get("readme", ""))

def validate_clone_args(args) -> bool:
    """Validate arguments for clone command"""
    try:
        missing_args = get_needed_args(args, ["course_id", "assignment_id"], True)
        if missing_args:
            need_argument_output("clone", missing_args)
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def _prepare_clone_parameters(args):
    """Extract and prepare parameters for clone command"""
    params = {
        'course_id': args.course_id,
        'assignment_id': args.assignment_id,
        'download_pdfs': args.download_pdfs,
        'download_docx': args.download_docx,
        'crawl_canvas_pages': args.crawl_canvas_pages,
        'delete_after_convert': args.delete_after_convert,
        'convert_to_markdown': args.convert_to_markdown,
        'integrate_together': args.integrate_together,
        'convert_links': args.convert_canvas_download_links,
        'output_file_destination': args.output_file_destination,
        'output_directory': args.output_directory,
        'display_in_terminal': args.display_in_terminal,
        'overwrite': args.overwrite_file,
        'do_save_main_file': args.output_file_destination is not None,
        'will_have_temp_files': ((args.download_pdfs or args.crawl_canvas_pages) and args.convert_to_markdown),
    }
    
    params['use_temp_dir'] = params['delete_after_convert'] and params['will_have_temp_files']
    params['download_dir'] = os.path.join(os.getcwd(), params['output_directory'], ".canvas.temp") if params['use_temp_dir'] else os.path.join(os.getcwd(), params['output_directory'])
    
    # Create download directory if needed
    if params['will_have_temp_files']:
        try:
            os.makedirs(params['download_dir'], exist_ok=True)
        except Exception as e:
            print(f"Error creating download directory: {e}")
    
    return params

def _get_api_client():
    """Initialize the Canvas API client"""
    try:
        return CanvasAPI()
    except ValueError as e:
        print(f"Error: {e}")
        return None

def _get_assignment_details(api, course_id, assignment_id):
    """Fetch assignment details from Canvas"""
    try:
        assignment = api.get_assignment_details(course_id, assignment_id)
        if not assignment:
            print(f"Assignment with ID {assignment_id} not found in course {course_id}.")
            return None
        
        description = assignment.get("description", None)
        if description is None:
            print(f"No description found for assignment {assignment_id} in course {course_id}.")
            return None
            
        return assignment
    except Exception as e:
        print(f"Error fetching assignment details: {e}")
        return None

def _process_html_content(api, assignment, params):
    """Process HTML content from assignment"""
    html = {'description': assignment.get("description", "")}
    fetched = set()
    
    # If crawl pages is enabled, fetch all canvas pages in the description recursively
    if params['crawl_canvas_pages']:
        _crawl_canvas_pages(api, html, fetched)
    
    # Convert links if requested
    if params['convert_links']:
        _convert_canvas_links(html)
        
    return {'html': html, 'fetched': fetched}

def _crawl_canvas_pages(api, html, fetched):
    """Recursively crawl canvas pages found in HTML content"""
    process_pages = list(html.values())
    
    while process_pages:
        page = process_pages.pop(0)
        try:
            from .config import Config
            canvas_url = Config.get_value("host", ["local", "global"])
            if canvas_url is None:
                print("Error: canvas_url not set in configuration.")
                return
            
            # Regular expression to match Canvas page links
            page_links = re.findall(
                r'<a [^>]*href="(https?:\/\/' + canvas_url.replace(".", r"\.") + r'\/courses\/\d+\/pages\/[^"]+)"[^>]*data-api-endpoint="([^"]+)"[^>]*data-api-returntype="Page"[^>]*>([^<]+)<\/a>',
                page,
                re.IGNORECASE,
            )
            
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
            print(f"Error during page crawling: {e}")

def _convert_canvas_links(html):
    """Convert Canvas links to more usable formats"""
    for title, content in html.items():
        try:
            from .config import Config
            canvas_url = Config.get_value("host", ["local", "global"])
            if canvas_url is None:
                print("Error: canvas_url not set in configuration.")
                return
            
            # Add Canvas link label to page links
            def add_canvas_link_label(match):
                return match.group(1) + match.group(2) + " (Canvas Link)" + match.group(3)

            content = re.sub(
                r'(<a [^>]*href="https?:\/\/' + canvas_url.replace(".", r"\.") + r'\/[^"]+"[^>]*data-api-endpoint="[^"]+"[^>]*data-api-returntype="Page"[^>]*>)([^<]+)(<\/a>)',
                add_canvas_link_label,
                content,
                flags=re.IGNORECASE,
            )
            
            # Add download links for file links
            def add_download_link(match):
                href = match.group(1)
                title = match.group(2)
                file_match = re.match(
                    r"(https:\/\/" + canvas_url.replace(".", r"\.") + r"\/courses\/\d+\/files\/\d+)\?verifier=([A-Za-z0-9]+)&amp;wrap=1", # type: ignore
                    href,
                )
                if file_match:
                    base_url, verifier = file_match.groups()
                    download_url = f"{base_url}/download?download_frd=1&verifier={verifier}"
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
            print(f"Error converting links: {e}")

def _find_file_links(html_content, file_type):
    """Find file links of specified type in HTML content"""
    file_links = {}
    try:
        from .config import Config
        canvas_url = Config.get_value("host", ["local", "global"])
        if canvas_url is None:
            print(f"Error: canvas_url not set in configuration.")
            return file_links
            
        for page in html_content['html'].values():
            pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+\.' + file_type + r')</a>'
            links = re.findall(pattern, page, re.IGNORECASE)
            
            for href, title in links:
                match = re.match(
                    r"(https:\/\/" + canvas_url.replace(".", r"\.") + r"\/courses\/\d+\/files\/\d+)\?verifier=([A-Za-z0-9]+)&amp;wrap=1",
                    href,
                )
                if match:
                    base_url, verifier = match.groups()
                    download_url = f"{base_url}/download?download_frd=1&verifier={verifier}"
                    file_links[title] = download_url
    except Exception as e:
        print(f"Error finding {file_type} links: {e}")
    
    return file_links

def _download_files(html_content, params, file_type):
    """Download files of specified type"""
    downloaded_files = []
    file_links = _find_file_links(html_content, file_type)
    
    try:
        for title, href in file_links.items():
            if href in html_content['fetched']:
                print(f"Already fetched {file_type.upper()} link: {href}")
                continue
            
            print(f"Found {file_type.upper()} link: {href}")
            filename = os.path.join(params['download_dir'], title)
            response = download_file(href, filename, overwrite=params['overwrite'])
            if response:
                html_content['fetched'].add(href)
                downloaded_files.append(filename)
    except Exception as e:
        print(f"Error downloading {file_type.upper()}: {e}")
    
    return downloaded_files

def _convert_to_markdown(html_content, pdfs, docs, params):
    """Convert content to markdown format"""
    if not params['convert_to_markdown']:
        return {"readme": html_content['html'].get("description", "")}
    
    markdown = {}
    readme = ""
    
    # Convert HTML to markdown
    if html_content['html']:
        try:
            from markitdown import MarkItDown
            import io
            md = MarkItDown(enable_plugins=True)
            
            for title, content in html_content['html'].items():
                content_stream = io.BytesIO(content.encode("utf-8")) if isinstance(content, str) else content
                result = md.convert_stream(content_stream)
                markdown_content = result.text_content
                    
                if title == "description":
                    readme = markdown_content
                else:
                    markdown[title] = "#" + title + "\n" + markdown_content
                
        except ImportError:
            _show_dependency_error("convert", "converting files")
            return {"readme": html_content['html'].get("description", "")}
    
    # Convert PDFs and DOCs to markdown
    for file_list, file_type in [(pdfs, "PDF"), (docs, "DOCX")]:
        if file_list:
            try:
                from markitdown import MarkItDown
                md = MarkItDown(enable_plugins=True)
                
                for file_path in file_list:
                    path_obj = Path(file_path)
                    if path_obj.suffix.lower() != f".{file_type.lower()}":
                        print(f"Skipping non-{file_type} file: {path_obj}")
                        continue
                    
                    result = md.convert(path_obj)
                    text = "#" + file_path + "\n" + result.text_content
                    markdown[file_path] = text
            except ImportError:
                _show_dependency_error("convert", "converting files")
                break
    
    # Integrate content if requested
    if params['integrate_together']:
        for key, value in markdown.items():
            if key == "description":
                continue
            readme = readme + "\n\n# " + key + "\n" + value
        markdown = {}
    
    return {"readme": readme, "markdown": markdown}

def _cleanup_temp_files(download_dir):
    """Clean up temporary downloaded files"""
    try:
        for file in os.listdir(download_dir):
            file_path = os.path.join(download_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(download_dir)
        print(f"Deleted temporary files in {download_dir}.")
    except Exception as e:
        print(f"Error deleting temporary files: {e}")

def _save_output(markdown_content, params):
    """Save markdown output to files"""
    if not params['do_save_main_file']:
        return
    
    try:
        readme = markdown_content.get("readme", "")
        if readme:
            output_path = Path(params['output_file_destination']).resolve()
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(readme)
            print(f"Saved markdown to {output_path}.")
                
        markdown_files = markdown_content.get("markdown", {})
        if markdown_files:
            output_dir = Path(params['output_directory']).resolve()
            os.makedirs(output_dir, exist_ok=True)
            
            for name, text in markdown_files.items():
                output_path = os.path.join(params['output_directory'], f"assignment_{params['assignment_id']}_{name}.md")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)
            print(f"Saved additional markdown files to {params['output_directory']}.")
        
    except Exception as e:
        print(f"Error saving markdown: {e}")

def _display_in_terminal(content):
    """Display markdown content in terminal"""
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        console.print(Markdown(content))
    except ImportError:
        _show_dependency_error("gui", "displaying tui")

def _show_dependency_error(dependency_type: str, operation_type: str):
    """Show dependency installation error message"""
    import importlib.metadata
    command_name = importlib.metadata.distribution("canvas-cmd").metadata["Name"]
    print(f"Error: Required dependencies for {operation_type} not found. Run 'pip install {command_name}[{dependency_type}]' to install them.")