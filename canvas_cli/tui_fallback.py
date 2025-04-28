# tui_fallback.py
# Simple fallback TUI using echo from handler_helper
from canvas_cli.handler_helper import echo, sort_courses, sort_assignments
from canvas_cli.tui_utils import EmojiIcons
import sys

def fallback_tui(courses, assignments=None, files=None, ctx=None):
    """
    Simple fallback TUI: print options and prompt for selection using input().
    Handles the full flow: course, assignment, file. Only prompts if more than one option.
    Returns tuple (course, assignment, file) or (course, None, None) etc.
    """
    icons = EmojiIcons()
    # Course selection
    if not courses:
        return None, None, None
    if len(courses) == 1:
        course = courses[0]
    else:
        echo("Select a course:", ctx)
        # Table header
        echo(f"{'#':<3} {'Fav':^3} {'Course Name':<40}", ctx)
        for idx, c in enumerate(courses):
            icon = icons.course_icon(c)
            fav = icons.star if c.get('is_favorite') else ''
            echo(f"{idx+1:<3} {fav:^3} {c.get('name','(no name)'):<40}", ctx)
        while True:
            try:
                sel = int(input("Enter course number: "))
                if 1 <= sel <= len(courses):
                    course = courses[sel-1]
                    break
            except Exception:
                pass
            echo("Invalid selection. Try again.", ctx)
    # Assignment selection (if provided)
    assignment = None
    if assignments:
        if len(assignments) == 1:
            assignment = assignments[0]
        else:
            echo(f"\nSelect an assignment for {course.get('name','')}:", ctx)
            # Table header
            echo(f"{'#':<3} {'✔':^3} {'Assignment Name':<40} {'Due':<16}", ctx)
            for idx, a in enumerate(assignments):
                icon = icons.assignment_icon(a)
                due = str(a.get('due_at') or '')[:16]
                echo(f"{idx+1:<3} {icon[:2]:^3} {a.get('name','(no name)'):<40} {due:<16}", ctx)
            while True:
                try:
                    sel = int(input("Enter assignment number: "))
                    if 1 <= sel <= len(assignments):
                        assignment = assignments[sel-1]
                        break
                except Exception:
                    pass
                echo("Invalid selection. Try again.", ctx)
    # File selection (if provided)
    file_path = None
    if files:
        if len(files) == 1:
            file_path = files[0]
        else:
            echo(f"\nSelect a file:", ctx)
            # Table header
            echo(f"{'#':<3} {'Type':^4} {'File Name':<40}", ctx)
            for idx, f in enumerate(files):
                icon = icons.folder if f.endswith('/') else icons.file
                echo(f"{idx+1:<3} {icon:^4} {f:<40}", ctx)
            echo("  [q] No file / skip file", ctx)
            while True:
                try:
                    sel = input("Enter file number or 'q' to skip: ").strip()
                    if sel.lower() == 'q':
                        file_path = None
                        break
                    sel = int(sel)
                    if 1 <= sel <= len(files):
                        file_path = files[sel-1]
                        break
                except Exception:
                    pass
                echo("Invalid selection. Try again.", ctx)
    return course, assignment, file_path
