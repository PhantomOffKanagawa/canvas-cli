# tui.py
# Main Text User Interface (TUI) for Canvas CLI
# Uses curses for a multi-page, mouse/keyboard-driven interface
# Features: fuzzy search, file navigation, table views, mouse hover, and more

import curses
import curses.textpad
import os
import re
import time
from unittest.mock import MagicMock
from canvas_cli.api import CanvasAPI
from canvas_cli.handler_helper import sort_courses, sort_assignments
from canvas_cli.tui_utils import format_course, format_assignment

# -----------------------------
# Fuzzy search helper function
# -----------------------------
def fuzzy_filter(items, query, key=lambda x: x):
    """
    Returns a filtered list of items where the key matches the fuzzy query.
    Uses a regex that matches all characters in order, but not necessarily consecutively.
    """
    if not query:
        return items
    pattern = '.*?'.join(map(re.escape, query))
    regex = re.compile(pattern, re.IGNORECASE)
    return [item for item in items if regex.search(key(item))]

# ---------------------------------------------------
# ListSelector: Generic scrollable/selectable list TUI
# ---------------------------------------------------
class ListSelector:
    """
    Displays a scrollable, searchable list (optionally as a table) and allows selection via keyboard or mouse.
    Supports fuzzy search, mouse hover, and ESC to go back.
    """
    def __init__(self, stdscr, items, title, key=lambda x: x, columns=None, mouse=False, allow_escape_back=False):
        self.stdscr = stdscr  # curses window
        self.items = items  # All items to display
        self.key = key  # Function to get display string from item
        self.title = title  # Title string
        self.selected = 0  # Currently selected index
        self.query = ''  # Current search query
        self.filtered = items  # Filtered items after search
        self.mouse = mouse  # Enable mouse support
        self.top = 0  # Top index for scrolling
        self.hovered = None  # Currently hovered index (for mouse)
        self.columns = columns  # List of (header, lambda, width) for table view
        self.allow_escape_back = allow_escape_back  # If True, ESC returns "__ESCAPE__"
        self.last_mouse_y = None  # Last mouse y position (for hover)

    def draw(self):
        """
        Draws the list/table, search bar, and highlights selection/hover.
        """
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        # Draw title and search bar
        self.stdscr.addstr(0, 0, self.title[:w-1], curses.A_BOLD)
        self.stdscr.addstr(1, 0, f"Search: {self.query}")
        max_items = h - (4 if self.columns else 3)
        # Draw table header if columns are defined
        if self.columns:
            # Only use columns with at least 3 elements (header, lambda, width)
            safe_columns = [col for col in self.columns if len(col) >= 3]
            col_line = " | ".join([f"{col[0]:<{col[2]}}" for col in safe_columns])
            self.stdscr.addstr(2, 0, col_line[:w-1], curses.A_UNDERLINE)
        # Scroll logic: keep selected in view
        if self.selected < self.top:
            self.top = self.selected
        elif self.selected >= self.top + max_items:
            self.top = self.selected - max_items + 1
        # Draw each visible row
        for idx, item in enumerate(self.filtered[self.top:self.top+max_items]):
            row = 3 + idx if self.columns else 2 + idx
            attr = curses.A_NORMAL
            # Highlight selected row
            if idx + self.top == self.selected:
                attr = curses.A_REVERSE
            # Dim highlight for hovered row (mouse)
            elif self.hovered is not None and idx + self.top == self.hovered:
                attr = curses.A_DIM | curses.A_REVERSE
            # Draw as table or simple list
            if self.columns:
                safe_columns = [col for col in self.columns if len(col) >= 3]
                col_line = " | ".join([
                    f"{str((col[1](item) or '') )[:col[2]]:<{col[2]}}" for col in safe_columns
                ])
                self.stdscr.addstr(row, 0, col_line[:w-1], attr)
            else:
                self.stdscr.addstr(row, 0, self.key(item)[:w-1], attr)
        self.stdscr.refresh()

    def handle_mouse(self, event):
        """
        Handles mouse events for hover and click selection.
        """
        _, y, _, _, bstate = event
        h, w = self.stdscr.getmaxyx()
        max_items = h - 4 if self.columns else h - 3
        row_offset = 3 if self.columns else 2
        idx = y - row_offset
        # If mouse is over a valid row, update hover and select on click
        if 0 <= idx < min(len(self.filtered)-self.top, max_items):
            self.hovered = self.top + idx
            if bstate & curses.BUTTON1_CLICKED:
                self.selected = self.hovered
                return True
        else:
            self.hovered = None
        return False

    def run(self):
        """
        Main event loop: handles keyboard/mouse, search, and returns selected item.
        ESC returns None or "__ESCAPE__" if allow_escape_back is set.
        """
        curses.curs_set(0)
        if self.mouse:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        while True:
            self.draw()
            ch = self.stdscr.getch()
            # Keyboard navigation
            if ch == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
            elif ch == curses.KEY_DOWN:
                self.selected = min(len(self.filtered)-1, self.selected + 1)
            elif ch in (curses.KEY_ENTER, 10, 13):
                return self.filtered[self.selected]
            elif ch == 27:  # ESC
                if self.allow_escape_back:
                    return "__ESCAPE__"
                return None
            # Mouse event
            elif ch == curses.KEY_MOUSE and self.mouse:
                try:
                    event = curses.getmouse()
                    if self.handle_mouse(event):
                        return self.filtered[self.selected]
                except Exception:
                    pass
            # Backspace (delete last char)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                self.query = self.query[:-1]
            # Ctrl+Backspace (delete last word)
            elif ch == 23:
                self.query = re.sub(r'\S+\s*$', '', self.query)
            # Add character to search
            elif 32 <= ch < 127:
                self.query += chr(ch)
            # Update filtered list
            self.filtered = fuzzy_filter(self.items, self.query, self.key)
            # Keep selection in bounds
            if self.selected >= len(self.filtered):
                self.selected = max(0, len(self.filtered)-1)
            # Mouse hover update (for terminals that support it)
            if self.mouse and self.last_mouse_y is not None:
                self.handle_mouse((0, self.last_mouse_y, 0, 0, 0))

# ---------------------------------------------------
# File selector: navigate folders and pick a file
# ---------------------------------------------------
def file_selector(stdscr, start_dir="."):
    """
    Lets the user navigate directories and select a file.
    Shows folders with 📁 and files with 📄, and allows going up with "..".
    Returns the full path to the selected file, or None if cancelled.
    """
    cwd = os.path.abspath(start_dir)
    while True:
        entries = []
        # Add parent directory entry if not at root
        if os.path.dirname(cwd) != cwd:
            entries.append("..")
        # List all files and folders in current directory
        for f in sorted(os.listdir(cwd)):
            full = os.path.join(cwd, f)
            if os.path.isdir(full):
                entries.append(f + "/")
            else:
                entries.append(f)
        # Table columns: icon and name
        file_cols = [
            ("Type", lambda x: "📁" if x.endswith("/") or x == ".." else "📄", 3),
            ("Name", lambda x: x, 32),
        ]
        sel = ListSelector(
            stdscr,
            entries,
            f"Select file in {cwd}",
            key=str,
            mouse=True,
            columns=file_cols,
            allow_escape_back=True
        )
        result = sel.run()
        # Handle navigation or selection
        if result is None or result == "__ESCAPE__":
            return None
        if result == "..":
            cwd = os.path.dirname(cwd)
        elif isinstance(result, str) and result.endswith("/"):
            cwd = os.path.join(cwd, result[:-1])
        elif isinstance(result, str):
            return os.path.join(cwd, result)

# ---------------------------------------------------
# Main TUI entrypoint: course, assignment, file select
# ---------------------------------------------------
def tui_main(stdscr):
    """
    Main TUI workflow: select course, then assignment, then file.
    Shows loading messages while waiting for API.
    """
    ctx = MagicMock()  # Dummy context for CanvasAPI
    api = CanvasAPI(ctx)
    # Helper to show a loading message centered on the screen
    def show_loading(msg):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h//2, max(0, (w-len(msg))//2), msg, curses.A_BOLD)
        stdscr.refresh()
    # Table columns for courses and assignments (header, lambda, width)
    course_cols = [
        ("Fav", lambda c: "★" if c.get("is_favorite") else "", 3),
        ("Name", lambda c: c.get("name", ""), 32),
        ("ID", lambda c: c.get("id", ""), 8),
        ("State", lambda c: c.get("workflow_state", ""), 10),
        ("Term", lambda c: c.get("term", {}).get("name", ""), 18),
        ("Start", lambda c: str(c.get("start_at") or '')[:10], 12),
        ("End", lambda c: str(c.get("end_at") or '')[:10], 12),
        ("Account", lambda c: c.get("account_id", ""), 8),
    ]
    assignment_cols = [
        # Mark as completed if 'submitted' or submission.workflow_state is submitted/graded
        ("✔", lambda a: "✔" if (a.get("submitted") or (a.get("submission") and a["submission"].get("workflow_state") in ["submitted", "graded"])) else ("✗" if a.get("missing") else ""), 3),
        ("Name", lambda a: a.get("name", ""), 32),
        ("ID", lambda a: a.get("id", ""), 8),
        ("Due", lambda a: str(a.get("due_at") or '')[:16], 18),
        ("Points", lambda a: a.get("points_possible", ""), 8),
        ("State", lambda a: a.get("workflow_state", ""), 10),
        ("Type", lambda a: (a.get("submission_types") or [""])[0], 12),
        ("Desc", lambda a: (str(a.get("description") or '')[:20] + ("..." if a.get("description") and len(str(a.get("description"))) > 20 else "")), 24),
    ]
    # Main course selection loop
    while True:
        show_loading("Loading courses from Canvas API...")
        courses = sort_courses(api.get_courses())
        course_sel = ListSelector(stdscr, courses, "Select course", key=format_course, mouse=True, columns=course_cols)
        course = course_sel.run()
        if not course or course == "__ESCAPE__":
            return
        # Assignment selection loop for chosen course
        while True:
            show_loading(f"Loading assignments for {course['name']}...")
            assignments = sort_assignments(api.get_assignments(course['id']))
            assign_sel = ListSelector(
                stdscr, assignments,
                f"Select assignment for {course['name']}",
                key=format_assignment, mouse=True, columns=assignment_cols, allow_escape_back=True
            )
            assignment = assign_sel.run()
            if not assignment or assignment == "__ESCAPE__":
                break
            # File selection page
            file_path = file_selector(stdscr)
            if not file_path:
                continue
            # Show summary and exit
            stdscr.clear()
            stdscr.addstr(0, 0, f"Selected course_id: {course['id']}")
            stdscr.addstr(1, 0, f"Selected assignment_id: {assignment['id']}")
            stdscr.addstr(2, 0, f"Selected file: {file_path}")
            stdscr.addstr(4, 0, "Press any key to exit.")
            stdscr.refresh()
            stdscr.getch()
            return

# -----------------------------
# Entrypoint for running TUI
# -----------------------------
def run_tui():
    """
    Entrypoint for running the TUI using curses.wrapper.
    """
    curses.wrapper(tui_main)

if __name__ == "__main__":
    run_tui()
