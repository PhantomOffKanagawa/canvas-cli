# tui.py
# Main Text User Interface (TUI) for Canvas CLI
# Uses curses for a multi-page, mouse/keyboard-driven interface
# Features: fuzzy search, file navigation, table views, mouse hover, and more

import curses
import curses.textpad
import os
import re
import time
import json
from unittest.mock import MagicMock
from canvas_cli.api import CanvasAPI
from canvas_cli.handler_helper import sort_courses, sort_assignments, echo
from canvas_cli.tui_utils import EmojiIcons
from canvas_cli.tui_fallback import fallback_tui
from handlers.config_handler import get_key

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

    @property
    def row_offset(self):
        return 3 if self.columns else 2

    @property
    def max_items(self):
        h, _ = self.stdscr.getmaxyx()
        return h - (4 if self.columns else 3)

    def draw(self):
        """
        Draws the list/table, search bar, and highlights selection/hover.
        """
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        # Draw title and search bar
        self.stdscr.addstr(0, 0, self.title[:w-1], curses.A_BOLD)
        self.stdscr.addstr(1, 0, f"Search: {self.query}")
        # Draw table header if columns are defined
        if self.columns:
            safe_columns = [col for col in self.columns if len(col) >= 3]
            col_line = " | ".join([
                f"{col[0]:^{col[2]}}" if col[2] <= 4 or col[0] in ("Type", "Fav", "✔") else f"{col[0]:<{col[2]}}"
                for col in safe_columns
            ])
            self.stdscr.addstr(2, 0, col_line[:w-1], curses.A_UNDERLINE)
        # Scroll logic: keep selected in view
        if self.selected < self.top:
            self.top = self.selected
        elif self.selected >= self.top + self.max_items:
            self.top = self.selected - self.max_items + 1
        # Draw each visible row
        for idx, item in enumerate(self.filtered[self.top:self.top+self.max_items]):
            row = self.row_offset + idx
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
                    f"{str((col[1](item) or '') )[:col[2]]:^{col[2]}}" if col[2] <= 4 or col[0] in ("Type", "Fav", "✔") else f"{str((col[1](item) or '') )[:col[2]]:<{col[2]}}"
                    for col in safe_columns
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
        idx = y - self.row_offset
        # If mouse is over a valid row, update hover and select on click
        if 0 <= idx < min(len(self.filtered)-self.top, self.max_items):
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
def file_selector(stdscr, start_dir=".", icons=None):
    """
    Lets the user navigate directories and select a file.
    Shows folders/files with icons based on emoji level, and allows going up with "..".
    Returns the full path to the selected file, or None if cancelled.
    """
    if icons is None:
        from canvas_cli.tui_utils import EmojiIcons
        icons = EmojiIcons()
    cwd = os.path.abspath(start_dir)
    while True:
        entries = []
        if os.path.dirname(cwd) != cwd:
            entries.append("..")
        for f in sorted(os.listdir(cwd)):
            full = os.path.join(cwd, f)
            if os.path.isdir(full):
                entries.append(f + "/")
            else:
                entries.append(f)
        file_cols = [
            ("Type", lambda x: icons.folder if x.endswith("/") or x == ".." else icons.file, 4),
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
def tui_main(
    stdscr,
    file_select_enabled=True,
    file_select_escape_behavior="back",  # 'back' or 'exit'
    start_page="course",  # 'course', 'assignment', 'file'
):
    """
    Main TUI workflow: select course, then assignment, then file.
    """
    # Load config for emoji level
    icons = EmojiIcons()
    ctx = MagicMock()  # Dummy context for CanvasAPI
    api = CanvasAPI(ctx)
    def show_loading(msg):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(h//2, max(0, (w-len(msg))//2), msg, curses.A_BOLD)
        stdscr.refresh()
    # Use tui_utils for icons and formatting
    course_cols = [
        ("Fav", lambda c: icons.star if c.get("is_favorite") else "", 4),
        ("Name", lambda c: c.get("name", ""), 32),
        ("ID", lambda c: c.get("id", ""), 8),
        ("State", lambda c: c.get("workflow_state", ""), 10),
        ("Term", lambda c: c.get("term", {}).get("name", ""), 18),
        ("Start", lambda c: str(c.get("start_at") or '')[:10], 12),
        ("End", lambda c: str(c.get("end_at") or '')[:10], 12),
        ("Account", lambda c: c.get("account_id", ""), 8),
    ]
    assignment_cols = [
        ("✔", lambda a: icons.format_assignment(a)[:2], 3),
        ("Name", lambda a: a.get("name", ""), 32),
        ("ID", lambda a: a.get("id", ""), 8),
        ("Due", lambda a: str(a.get("due_at") or '')[:16], 18),
        ("Points", lambda a: a.get("points_possible", ""), 8),
        ("State", lambda a: a.get("workflow_state", ""), 10),
        ("Type", lambda a: (a.get("submission_types") or ["any"])[0], 12),
        # ("Desc", lambda a: (str(a.get("description") or '')[:20] + ("..." if a.get("description") and len(str(a.get("description"))) > 20 else "")), 24),
    ]
    course = assignment = file_path = None
    page = start_page
    while True:
        if page == "course":
            show_loading("Loading courses from Canvas API...")
            courses = sort_courses(api.get_courses())
            course_sel = ListSelector(stdscr, courses, "Select course", key=icons.format_course, mouse=True, columns=course_cols)
            course = course_sel.run()
            if not course or course == "__ESCAPE__":
                return None, None, None
            page = "assignment"
        elif page == "assignment":
            if not course:
                return None, None, None
            show_loading(f"Loading assignments for {course.get('name', '')}...")
            assignments = sort_assignments(api.get_assignments(course.get('id')))
            assign_sel = ListSelector(
                stdscr, assignments,
                f"Select assignment for {course.get('name', '')}",
                key=icons.format_assignment, mouse=True, columns=assignment_cols, allow_escape_back=True
            )
            assignment = assign_sel.run()
            if not assignment:
                page = "course"
                continue
            if assignment == "__ESCAPE__":
                page = "course"
                continue
            page = "file" if file_select_enabled else "done"
        elif page == "file":
            file_path = file_selector(stdscr, icons=icons)
            if not file_path:
                if file_select_escape_behavior == "exit":
                    return course, assignment, None
                else:
                    page = "assignment"
                    continue
            return course, assignment, file_path
        elif page == "done":
            return course, assignment, file_path

def run_tui(
    file_select_enabled=True,
    file_select_escape_behavior="back",
    start_page="course",
    ctx=None,
):
    """
    Entrypoint for running the TUI using curses.wrapper or fallback echo-based TUI.
    Args:
        file_select_enabled: if False, skip file select page
        file_select_escape_behavior: 'back' (go back to assignment) or 'exit' (return course/assignment, no file)
        start_page: which page to start on ('course', 'assignment', 'file')
        ctx: typer.Context (required)
    Returns:
        (course, assignment, file) or (course, assignment, None) if file select is escaped with 'exit'
    """
    if ctx is None:
        raise ValueError("ctx (typer.Context) is required for run_tui. It must contain Canvas API token and host.")
    # Ensure token and host are present
    token = get_key("token", ctx)
    host = get_key("host", ctx)
    if not token or not host:
        echo("Error: Missing token or host in context.", ctx=ctx, level="error")
        return None, None, None
    
    fallback = get_key("tui_fallback", ctx)
    if fallback:
        from canvas_cli.api import CanvasAPI
        api = CanvasAPI(ctx)
        courses = sort_courses(api.get_courses())
        if not courses:
            return None, None, None
        course = None
        assignment = None
        file_path = None
        assignments = None
        files = None
        course, _, _ = fallback_tui(courses, ctx=ctx)
        if not course:
            return None, None, None
        assignments = sort_assignments(api.get_assignments(course.get('id')))
        assignment = None
        file_path = None
        if assignments:
            assignment, _, _ = fallback_tui([course], assignments, ctx=ctx)
            if not assignment:
                return course, None, None
        if file_select_enabled:
            import os
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            _, _, file_path = fallback_tui([course], [assignment] if assignment else None, files, ctx=ctx)
        return course, assignment, file_path
    # Otherwise, use curses TUI
    result = {}
    def tui_wrapper(stdscr):
        result['value'] = tui_main(
            stdscr,
            file_select_enabled=file_select_enabled,
            file_select_escape_behavior=file_select_escape_behavior,
            start_page=start_page,
        )
    curses.wrapper(tui_wrapper)
    return result.get('value')

if __name__ == "__main__":
    run_tui()
