# tui_utils.py
# Utilities for formatting and icons for TUI

# -----------------------------
# Course icon formatting helper
# -----------------------------
def course_icon(course):
    """
    Returns a string with icons representing course status:
    - Star if favorited
    - Green dot if available, white if not
    """
    icon = ""
    # Add star if course is favorited
    if course.get("is_favorite"):
        icon += "★ "
    else:
        icon += "  "
    # Add green dot if course is available, else white dot
    if course.get("workflow_state") == "available":
        icon += "🟢 "
    else:
        icon += "⚪ "
    return icon

# -----------------------------------
# Assignment icon formatting helper
# -----------------------------------
def assignment_icon(assignment):
    """
    Returns a string with icons representing assignment status:
    - Check if completed/submitted
    - X if missing
    - Medal if graded
    """
    icon = ""
    # Mark as completed if 'submitted' is True
    if assignment.get("submitted"):
        icon += "✔ "
    # Mark as missing if 'missing' is True
    elif assignment.get("missing"):
        icon += "✗ "
    else:
        icon += "  "
    # Add medal if assignment is graded
    if assignment.get("graded"):
        icon += "🏅 "
    return icon

# -----------------------------------
# Format a course for display in TUI
# -----------------------------------
def format_course(course):
    """
    Returns a formatted string for a course, including icons and name.
    """
    return f"{course_icon(course)}{course['name']}"

# ---------------------------------------
# Format an assignment for display in TUI
# ---------------------------------------
def format_assignment(assignment):
    """
    Returns a formatted string for an assignment, including icons and name.
    """
    return f"{assignment_icon(assignment)}{assignment['name']}"
