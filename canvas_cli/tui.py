"""
Terminal User Interface (TUI) for Canvas CLI
Provides interactive TUI components for selecting courses and assignments
"""

from typing import List, Dict, Optional, Tuple, Callable
from .tui_utils import FuzzySearch, Formatter
from .api import CanvasAPI

# Try to import curses, but provide fallback if not available
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False
    import importlib.metadata
    command_name = importlib.metadata.distribution("canvas-cmd").metadata["Name"]
    print(f"Curses module not available. Using fallback text ui.\nIf on Windows run `pip install {command_name}[windows]` to download windows-curses for tui support.")

# Import curses module inside the conditional block to avoid unbound references
if CURSES_AVAILABLE:
    import curses
    
    class SelectionList:
        """Interactive list for selecting items in TUI"""
        
        def __init__(self, items: List[Dict], title: str):
            """Initialize the selection list
            
            Args:
                items: List of items to display
                title: Title of the selection list
            """
            self.items = items
            self.filtered_items = items.copy()
            self.title = title
            self.selected_idx = 0
            self.offset = 0
            self.search_text = ""
            self.search_mode = False
            
        def handle_key(self, key: int) -> Optional[Dict]:
            """Handle a key press and return the selected item if Enter is pressed"""
            # Auto-enable search for any printable character
            if not self.search_mode and 32 <= key <= 126 and key != ord('q'):
                self.search_mode = True
                self.search_text = chr(key)
                self._update_filtered_items()
                return None
                
            if key == curses.KEY_UP:
                self.selected_idx = max(0, self.selected_idx - 1)
            elif key == curses.KEY_DOWN:
                self.selected_idx = min(len(self.filtered_items) - 1, self.selected_idx + 1)
            elif key == curses.KEY_ENTER or key == 10:  # Enter key
                if self.filtered_items:
                    return self.filtered_items[self.selected_idx]
            elif key == 27:  # Escape key - handled outside
                pass
            elif self.search_mode:
                if key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Support multiple backspace codes
                    if self.search_text:
                        self.search_text = self.search_text[:-1]
                        self._update_filtered_items()
                elif 32 <= key <= 126:  # Printable ASCII characters
                    self.search_text += chr(key)
                    self._update_filtered_items()
                    
            return None
            
        def _update_filtered_items(self):
            """Update filtered items based on search text with fuzzy matching"""
            self.filtered_items = FuzzySearch.filter_and_sort_items(self.items, self.search_text)
            self.selected_idx = 0
            
        def render(self, stdscr, y: int, x: int, height: int, width: int, type: str | None = None, formatter: Callable | None = None) -> None:
            """Render the selection list"""
            # Adjust offset if selected item is out of view
            if self.selected_idx < self.offset:
                self.offset = self.selected_idx
            if self.selected_idx >= self.offset + height - 2:
                self.offset = self.selected_idx - height + 3
                
            # Draw title and box
            stdscr.attron(curses.color_pair(Formatter.COLORS_HEADER) | curses.A_BOLD)
            stdscr.addstr(y, x, f" {self.title} ")
            stdscr.attroff(curses.color_pair(Formatter.COLORS_HEADER) | curses.A_BOLD)
            
            stdscr.addstr(y, x + len(self.title) + 2, f" ({len(self.filtered_items)} items)")
            
            # Draw search status if active
            if self.search_mode:
                search_status = f" Search: {self.search_text}"
                stdscr.addstr(y, x + width - len(search_status) - 2, search_status)
            
            # Draw items
            max_display = min(height - 2, len(self.filtered_items))
            for i in range(max_display):
                item_idx = i + self.offset
                if item_idx < len(self.filtered_items):
                    item = self.filtered_items[item_idx]
                    
                    # Highlight selected item
                    if item_idx == self.selected_idx:
                        stdscr.attron(curses.A_REVERSE)
                    else:
                        stdscr.attron(curses.color_pair(Formatter.get_color(item)))
                    
                    selected = self.selected_idx == item_idx
                    if type == "courses" or type == "assignments":
                        Formatter.write_item(stdscr, y + i + 1, x + 1, width, item, type, selected)
                    elif formatter:
                        stdscr.addstr(y + i + 1, x + 1, formatter(item, type)[:width-2])
                    else:
                        stdscr.addstr(y + i + 1, x + 1, str(item)[:width-2])
                    
                    if item_idx == self.selected_idx:
                        stdscr.attroff(curses.A_REVERSE)
                    else:
                        stdscr.attroff(curses.color_pair(Formatter.get_color(item)))
            
            # Draw scrollbar if needed
            if len(self.filtered_items) > height - 2:
                scrollbar_height = max(1, (height - 2) * (height - 2) // len(self.filtered_items))
                scrollbar_pos = (height - 2) * self.offset // len(self.filtered_items)
                for i in range(height - 2):
                    if scrollbar_pos <= i < scrollbar_pos + scrollbar_height:
                        stdscr.addstr(y + i + 1, x + width - 1, "█")
                    else:
                        stdscr.addstr(y + i + 1, x + width - 1, "│")

    # Improved show_message function that's more robust
    def show_message(stdscr, message, wait_for_key=True):
        """Show a message on the screen
        
        Args:
            stdscr: Curses window
            message: Message to display
            wait_for_key: Whether to wait for a key press
        """
        # Save current cursor state
        try:
            old_cursor = curses.curs_set(0)  # Hide cursor
        except:
            old_cursor = 0
            
        try:
            # Clear the screen
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Split message into lines
            lines = message.split('\n')
            
            # Center each line vertically and horizontally
            for i, line in enumerate(lines):
                if i < height - 1:  # Leave space for "Press any key" message
                    y_pos = (height - len(lines)) // 2 + i
                    x_pos = max((width - len(line)) // 2, 0)
                    safe_line = line[:width-1] if len(line) > width-1 else line
                    if 0 <= y_pos < height - 1:
                        stdscr.addstr(y_pos, x_pos, safe_line)
            
            # Add press any key message if waiting for key
            if wait_for_key:
                prompt = "Press any key to continue..."
                stdscr.addstr(min(len(lines) + 1, height-1), 0, prompt[:width-1])
                
            # Update the screen
            stdscr.refresh()
            
            # Wait for user input if requested
            if wait_for_key:
                stdscr.getch()
        except curses.error:
            # Handle any curses errors
            pass
        finally:
            # Restore cursor state
            try:
                curses.curs_set(old_cursor)
            except:
                pass
            
    def select_course_and_assignment(stdscr) -> Tuple[Optional[Dict], Optional[Dict]]:
        """TUI for selecting a course and assignment"""
        # Set up curses
        curses.curs_set(0)  # Hide cursor
        stdscr.clear()
        
        # Get terminal dimensions
        height, width = stdscr.getmaxyx()
        
        # Initialize Canvas API
        try:
            api = CanvasAPI()
        except ValueError as e:
            show_message(stdscr, f"{str(e)}\nPress any key to exit...")
            return None, None
        
        # Create formatter instance
        formatter = Formatter()
        
        # Get courses
        show_message(stdscr, "Loading courses...", wait_for_key=False)
        courses = api.get_courses()
        
        if not courses:
            show_message(stdscr, "No courses found. Press any key to exit...")
            return None, None
        
        # Main selection loop
        while True:
            # Set up course selection list
            course_list = SelectionList(
                items=courses,
                title="Select a Course",
            )
            
            # Course selection loop
            selected_course = None
            while True:
                stdscr.clear()
                
                # Show help text
                help_text = "↑/↓: Navigate | Enter: Select | Type to search | Esc: Quit"
                stdscr.addstr(height - 1, 0, help_text[:width-1])
                
                # Show legend
                legend = f"{formatter.ICON_FAVORITE}: Favorite"
                stdscr.attron(curses.color_pair(Formatter.COLORS_FAVORITE))
                stdscr.addstr(height - 1, width - len(legend) - 1, legend[:width-1])
                stdscr.attroff(curses.color_pair(Formatter.COLORS_FAVORITE))
                
                # Render course list
                course_list.render(stdscr, 0, 0, height - 2, width, "courses")
                
                # Refresh screen
                stdscr.refresh()
                
                # Get user input
                key = stdscr.getch()
                
                # Handle key
                if key == 27:  # Escape key - exit whole TUI
                    return None, None
                
                result = course_list.handle_key(key)
                if result:
                    selected_course = result
                    break
            
            # Course selected, get assignments
            course_id = selected_course.get('id')
            if course_id is None:
                show_message(stdscr, "Error: Course ID not found", wait_for_key=True)
                continue  # Go back to course selection
            
            show_message(stdscr, f"Loading assignments for {selected_course.get('name')}...", wait_for_key=False)
            assignments = api.get_assignments(course_id)
            
            if not assignments:
                show_message(stdscr, "No assignments found for this course. Press any key to continue...")
                continue  # Go back to course selection
            
            # Set up assignment selection list
            assignment_list = SelectionList(
                items=assignments,
                title=f"Select an Assignment for {selected_course.get('name')}",
            )
            
            # Assignment selection loop
            selected_assignment = None
            while True:
                stdscr.clear()
                
                # Show help text
                help_text = "↑/↓: Navigate | Enter: Select | Type to search | Esc: Back"
                stdscr.addstr(height - 1, 0, help_text[:width-1])
                
                # Show legend
                legend_submitted = f"{formatter.ICON_SUBMITTED}: Submitted"
                legend_past_due = f"{formatter.ICON_PAST_DUE}: Past Due"
                legend_locked = f"{formatter.ICON_LOCKED}: Locked"
                
                # Calculate positions for legend items
                legend_width = len(legend_submitted) + len(legend_past_due) + len(legend_locked) + 6
                legend_start = width - legend_width - 1
                
                # Draw legend items with appropriate colors
                stdscr.attron(curses.color_pair(Formatter.COLORS_SUBMITTED))
                stdscr.addstr(height - 1, legend_start, legend_submitted)
                stdscr.attroff(curses.color_pair(Formatter.COLORS_SUBMITTED))
                
                stdscr.attron(curses.color_pair(Formatter.COLORS_PAST_DUE))
                stdscr.addstr(height - 1, legend_start + len(legend_submitted) + 2, legend_past_due)
                stdscr.attroff(curses.color_pair(Formatter.COLORS_PAST_DUE))
                
                stdscr.attron(curses.color_pair(Formatter.COLORS_LOCKED))
                stdscr.addstr(height - 1, legend_start + len(legend_submitted) + len(legend_past_due) + 4, legend_locked)
                stdscr.attroff(curses.color_pair(Formatter.COLORS_LOCKED))
                
                # Render assignment list
                assignment_list.render(stdscr, 0, 0, height - 2, width, "assignments")
                
                # Refresh screen
                stdscr.refresh()
                
                # Get user input
                key = stdscr.getch()
                
                # Handle key
                if key == 27:  # Escape key - go back to course selection
                    break  # This breaks out of assignment loop, but stays in course loop
                
                result = assignment_list.handle_key(key)
                if result:
                    selected_assignment = result
                    # Return both selected course and assignment to exit the TUI
                    return selected_course, selected_assignment
            
            # If we get here, user pressed Escape to go back to course selection
            # We'll loop back to the course selection

# Fallback text-based interface for when curses is not available
def select_from_list(items, display_func, title, all_items=None) -> Optional[Dict]:
    """Simple text-based selection interface with fuzzy search"""
    print(f"\n--- {title} ---")
    
    # Display all items with indices
    for i, item in enumerate(items):
        print(f"{i+1}. {display_func(item, 'courses' if 'course_code' in item else 'assignments')}")
    
    # Get user selection
    while True:
        try:
            # Allow for search with /
            choice = input("\nEnter number to select, or /search_term to search, or q to quit: ")
            
            # Handle search
            if choice.startswith('/'):
                search_term = choice[1:].lower()
                if not search_term:
                    continue
                
                # Filter and sort all items by search term
                filtered_items = FuzzySearch.filter_and_sort_items(all_items or items, search_term)
                
                if not filtered_items:
                    print(f"No matches found for '{search_term}'")
                    continue
                
                # Recursively call with filtered items but pass in full list
                return select_from_list(filtered_items, display_func, f"{title} (filtered)", all_items=items)
            
            # Handle quit
            if choice.lower() == 'q':
                return None
                
            # Handle numeric selection
            index = int(choice) - 1
            if 0 <= index < len(items):
                return items[index]
            else:
                print(f"Please enter a number between 1 and {len(items)}")
        except ValueError:
            print("Please enter a valid number or search term")
        except KeyboardInterrupt:
            print("\nSearch cancelled.")
            return None

def text_select_course_and_assignment() -> Tuple[Optional[Dict], Optional[Dict]]:
    """Simple text-based selection interface for courses and assignments"""
    # Initialize Canvas API
    try:
        api = CanvasAPI()
    except ValueError as e:
        print(f"Error: {e}")
        return None, None
        
    # Get courses
    print("Loading courses...")
    courses = api.get_courses()
    
    if not courses:
        print("No courses found.")
        return None, None
    
    # Select a course
    selected_course = select_from_list(courses, Formatter.format_item, "Select a Course")
    
    if not selected_course:
        return None, None
        
    # Get assignments for the selected course
    print(f"\nLoading assignments for {selected_course.get('name')}...")
    course_id = selected_course.get('id')
    if course_id is None:
        print("Error: Course ID not found")
        return None, None
    assignments = api.get_assignments(int(course_id))
    
    if not assignments:
        print("No assignments found for this course.")
        return selected_course, None
        
    # Select an assignment
    selected_assignment = select_from_list(
        assignments, 
        Formatter.format_item, 
        f"Select an Assignment for {selected_course.get('name')}"
    )
    
    return selected_course, selected_assignment


def select_file(start_dir: str | None = None, title: str = "Select a File", fallback=False) -> Optional[str]:
    """File selector that allows navigating directories and selecting a file
    
    Args:
        start_dir: Directory to start in (defaults to current directory)
        title: Title to display above the selection list
        fallback: Whether to force fallback to text-based interface
        
    Returns:
        The selected file path or None if cancelled
    """
    import os
    from pathlib import Path
    
    # Start in current directory if not specified
    current_dir = Path(start_dir).resolve() if start_dir else Path.cwd()
    selected_path = None
    
    while True:
        # Get directory contents
        items = [] # List to hold directory entries
        try:
            # Create list of parent directory entry
            if current_dir.parent != current_dir:  # Not at root
                items.append({
                    'name': '..',
                    'path': str(current_dir.parent),
                    'is_dir': True,
                    'size': '',
                    'modified': ''
                })
            
            # Add directories first
            for entry in sorted(os.scandir(current_dir), key=lambda e: (not e.is_dir(), e.name.lower())):
                items.append({
                    'name': entry.name,
                    'path': str(Path(entry.path)),
                    'is_dir': entry.is_dir(),
                    'size': '' if entry.is_dir() else os.path.getsize(entry.path),
                    'modified': os.path.getmtime(entry.path)
                })
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error accessing directory: {e}")
            
        # Define display function
        def format_file_entry(item, _):
            prefix = '[d] ' if item.get('is_dir') else '(f) '
            size = '' if item.get('is_dir') else f" ({item.get('size', 0) / 1024:.1f} KB)"
            return f"{prefix}{item.get('name')}{size}"
            
        # Show current path in title
        path_title = f"{title} - {current_dir}"
        
        # Use select_from_options to display the file list
        selected = select_from_options(items, 'name', path_title, fallback, formatter=format_file_entry)
        
        if selected is None:
            return None  # User cancelled
            
        # If directory, navigate to it. If file, return it.
        if selected.get('is_dir'):
            path_str = selected.get('path')
            if path_str is not None:
                current_dir = Path(path_str)
            else:
                print("Error: Path not found")
                return None
        else:
            return selected.get('path')  # Return the selected file path

def select_from_options(options: List[Dict], label_key: str | None, title: str = "Select an option", fallback=False, formatter=None) -> Optional[Dict]:
    """Present a list of options to the user and return the selected one
    
    Args:
        options: List of dictionary objects to select from
        label_key: Key to use for displaying each option
        title: Title to display above the selection list
        fallback: Whether to force fallback to text-based interface
        formatter: Custom formatter function for displaying items
        
    Returns:
        The selected dictionary object or None if cancelled
    """
    # Handle empty options list
    if not options:
        print("No options available.")
        return None
        
    # Define display function for the options
    if formatter is None:
        def display_option(item, _):
            return f"{item.get(label_key, 'No label')}"
        formatter = display_option
        
    # Use appropriate interface based on curses availability
    try:
        if CURSES_AVAILABLE and not fallback:
            # Use curses-based selection
            def select_with_curses(stdscr) -> Optional[Dict]:
                # Set up curses
                curses.curs_set(0)  # type: ignore # Hide cursor
                stdscr.clear()
                
                # Get terminal dimensions
                height, width = stdscr.getmaxyx()
                
                # Set up selection list
                option_list = SelectionList(
                    items=options,
                    title=title,
                )
                
                # Selection loop
                while True:
                    stdscr.clear()
                    
                    # Show help text
                    help_text = "↑/↓: Navigate | Enter: Select | Type to search | Esc: Cancel"
                    stdscr.addstr(height - 1, 0, help_text[:width-1])
                    
                    # Render option list
                    option_list.render(stdscr, 0, 0, height - 2, width, formatter=formatter)
                    
                    # Refresh screen
                    stdscr.refresh()
                    
                    # Get user input
                    key = stdscr.getch()
                    
                    # Handle key
                    if key == 27:  # Escape key - cancel
                        return None
                    
                    result = option_list.handle_key(key)
                    if result:
                        return result
            
            return curses.wrapper(select_with_curses) # type: ignore
        else:
            # Use text-based selection
            return select_from_list(options, formatter, title)
    except Exception as e:
        print(f"Error during selection: {e}")
        return None

def run_tui(fallback=False) -> Tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """Run the TUI to select a course and assignment
    
    Args:
        fallback: Whether to force fallback to text-based interface
        
    Returns:
        A tuple of (course_id, assignment_id, course_name, assignment_name)
    """
    try:
        # Use appropriate interface based on curses availability
        if CURSES_AVAILABLE and not fallback:
            course, assignment = curses.wrapper(select_course_and_assignment) # type: ignore
        else:
            course, assignment = text_select_course_and_assignment()
            
        if course and assignment:
            return (
                course.get('id'),
                assignment.get('id'),
                course.get('name'),
                assignment.get('name')
            )
        else:
            print("Selection cancelled or no items selected.")
            return None, None, None, None
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, None, None
