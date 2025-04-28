# tui_utils.py
# Utilities for formatting and icons for TUI

from datetime import datetime
from handlers.config_handler import get_key_static

# -----------------------------
# Emoji level logic
# -----------------------------

def get_emoji_level():
    """
    Returns 2 if full emoji (can see 📁), 1 if ascii/partial emoji (can see ✔), 0 if plain text only.
    """
    level = get_key_static('tui_emoji_level')
    if level is None:
        return 0  # Default to plain text if not set
    else:
        return int(level)
    
class EmojiIcons:
    """
    Centralized icon set for the TUI, based on emoji level (0=plain, 1=ascii, 2=emoji).
    Usage: icons = EmojiIcons(); icons.folder, icons.file, icons.check, ...
    Now also provides icon-formatting methods for course/assignment/file rows.
    """
    def __init__(self):
        lvl = get_emoji_level()
        # Folder/File
        self.folder = "📁" if lvl == 2 else ("DIR" if lvl == 1 else "DIR")
        self.file = "📄" if lvl == 2 else ("F" if lvl == 1 else "F")
        # Booleans
        self.check = "✔" if lvl >= 1 else "Y"
        self.cross = "✗" if lvl >= 1 else "N"
        # Star/favorite
        self.star = "★" if lvl == 2 else "*"
        # Dots (status)
        self.dot_green = "🟢" if lvl == 2 else ("O" if lvl == 1 else ".")
        self.dot_white = "⚪" if lvl == 2 else ("." if lvl == 1 else ".")
        # Medal (graded)
        self.medal = "🏅" if lvl == 2 else "G"
    def dot(self, color):
        return self.dot_green if color == 'green' else self.dot_white
    def course_icon(self, course):
        icon = ""
        icon += self.star + " " if course.get("is_favorite") else "  "
        icon += self.dot('green' if course.get("workflow_state") == "available" else 'white') + " "
        return icon
    def assignment_icon(self, assignment):
        icon = ""
        if assignment.get("has_submitted_submissions"):
            icon += self.check + " "
        elif assignment.get("due_at") and assignment.get("due_at") < datetime.now().isoformat() and not assignment.get("has_submitted_submissions"):
            icon += self.cross + " "
        else:
            icon += "  "
        if assignment.get("graded") and hasattr(self, 'medal'):
            icon += self.medal + " "
        return icon
    def format_course(self, course):
        return f"{self.course_icon(course)}{course['name']}"
    def format_assignment(self, assignment):
        return f"{self.assignment_icon(assignment)}{assignment['name']}"

