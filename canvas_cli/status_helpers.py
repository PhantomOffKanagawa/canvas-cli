"""
Helper functions for the Canvas CLI status command
"""

import json
from math import ceil
import random

from canvas_cli.api import format_date
import shutil

def show_global_status(api, args: dict) -> None:
    """Show grade status for all courses with improved terminal formatting

    Args:
        api: CanvasAPI instance
        json_output: Whether to output in JSON format
    """

    print("Fetching all course grades...")
    params = {
        'enrollment_state': 'active',
        'include[]': ['total_scores', 'favorites', 'sections'],
        'per_page': 100
    }
    courses = api.get_courses(params)

    if not courses:
        print("No active courses found.")
        return

    if args['output_json']:
        print(json.dumps(courses, indent=2))
        return

    # Only show favorite courses
    courses = [course for course in courses if course.get('is_favorite', False)]
    names = [course.get('name', '') or course.get('original_name', '') or course.get('course_code', 'Unknown Course') for course in courses]

    # Terminal width for formatting
    term_size = shutil.get_terminal_size((80, 20))
    term_width = term_size.columns
    # term_height = term_size.lines

    # Section Sizes
    sizes = {
        "grade": len('100.0% (A+)') + 2,  # Max Size Message ' 100.0% (A+) '
    }

    if term_width < 120 or not args['show_messages']:
        # No room for messages
        sizes['messages'] = 0
        sizes['course'] = term_width // 3 - 3  # 3 columns
        sizes['progress'] = term_width - sizes['course'] - sizes['messages'] - sizes['grade'] - 2 - 3 - 1 # - 2 for progress seperator, - 2 for grade seperator and |, -1 idk
    else:
        sizes['messages'] = term_width // 3 - 2  # 1 side exposed but progress now side added
        sizes['course'] = term_width // 4 - 2  # 1 side exposed + |
        sizes['progress'] = term_width - sizes['course'] - sizes['messages'] - sizes['grade'] - 2 - 3 - 4 # - 2 for progress seperator, - 2 for grade seperator and |, -4 idk

    # Remaining space for progress bar

    # Fun messages for different grade ranges
    grade_messages = {
        'A+': ["You're absolutely crushing it! 🌟", "A+ performance! Keep being amazing!", "Wow! You're in a league of your own!"],
        'A': ["Excellent work! You're acing this!", "A-mazing job you're doing!", "Top-notch performance! 🏆"],
        'A-': ["Nearly perfect! Just a tiny bit more!", "Fantastic work with room to grow!", "So close to perfection!"],
        'B+': ["Very good performance! Almost there!", "B+ is still pretty awesome!", "Solid work with potential for more!"],
        'B': ["Good job! Keep pushing forward!", "Solid B performance!", "You're doing well, but don't stop now!"],
        'B-': ["Not bad! Let's aim a bit higher!", "Good effort with room for improvement!", "You've got this, just need more focus!"],
        'C+': ["You're hanging in there!", "Time to step it up a bit!", "A bit more effort will go a long way!"],
        'C': ["Let's work on improving this!", "Average performance - you can do better!", "Time to buckle down and focus!"],
        'C-': ["Things are getting concerning!", "Warning zone - time to study more!", "Let's turn this around, shall we?"],
        'D+': ["This needs immediate attention!", "Serious studying needed ASAP!", "Time for a study emergency plan!"],
        'D': ["⚠️ Danger zone! Major improvements needed!", "Time to reconsider your study habits!", "Let's talk about tutoring options!"],
        'F': ["🚨 Critical situation! Time for drastic measures!", "Emergency study intervention needed!", "Let's schedule a meeting with your advisor!"]
    }

    def get_message(grade):
        if not grade:
            return "N/A"
        base_grade = grade[0]
        if grade in grade_messages:
            messages = grade_messages[grade]
        elif base_grade in ['A', 'B', 'C', 'D', 'F']:
            matching_messages = []
            for g, msgs in grade_messages.items():
                if g.startswith(base_grade):
                    matching_messages.extend(msgs)
            messages = matching_messages or ["Keep working at it!"]
        else:
            messages = ["Keep working at it!"]
        return random.choice(messages)

    # Header
    title = " Overall Academic Status "
    print("\n" + title.center(term_width, "="))
    if sizes['messages'] > 0:
        print(f"{'Course':<{sizes['course']}} │ {'Grade':^{sizes['grade']}} │ {'Progress':^{sizes['progress']}} │ {'Message ':>{sizes['messages']}}")
    else:
        print(f"{'Course':<{sizes['course']}} │ {'Grade':^{sizes['grade']}} │ {'Progress':^{sizes['progress']}}")
    print("-" * term_width)

    for i, course in enumerate(courses):
        # Prefer nickname, then course_code, then name
        nickname = names[i]
        nickname = nickname[:sizes['course']]
        enrollments = course.get('enrollments', [])

        if enrollments:
            enrollment = enrollments[0]
            letter_grade = enrollment.get('computed_current_letter_grade')
            score = enrollment.get('computed_current_score')

            # Color selection
            grade_color = '\033[92m'  # Green
            if letter_grade and letter_grade.startswith('C'):
                grade_color = '\033[93m'  # Yellow
            elif letter_grade and (letter_grade.startswith('D') or letter_grade.startswith('F')):
                grade_color = '\033[91m'  # Red
            reset_color = '\033[0m'

            # Grade text
            if score is not None:
                grade_text = f"{grade_color}{score:.1f}% ({letter_grade or 'N/A'}){'' if letter_grade.endswith('+') else ' '}{reset_color}"
                # Progress bar
                filled = ceil((min(100, score) / 100) * sizes['progress'])
                empty = sizes['progress'] - filled
                bar_color = grade_color
                bar = f"{bar_color}{'█' * filled}{' ' * empty}{reset_color}"
                message = get_message(letter_grade)
            else:
                grade_text = f"{grade_color}N/A{reset_color}"
                bar = f"\033[90m{' ' * sizes['progress']}{reset_color}"
                message = "No grade available"

        else:
            grade_text = f"\033[90mN/A{reset_color}"
            bar = f"\033[90m{' ' * sizes['progress']}{reset_color}"
            message = "No enrollment data"

        if sizes['messages'] > 0:
            trimmed_message = message[:sizes['messages']]
            print(f"{nickname:<{sizes['course']}} │ {grade_text:>{sizes['grade'] + len(grade_color) + len(reset_color)}} │ {bar} │ {trimmed_message}")
        else:
            print(f"{nickname:<{sizes['course']}} │ {grade_text:>{sizes['grade'] + len(grade_color) + len(reset_color)}} │ {bar}")

    print("=" * term_width)
    print("Use --json for complete details".center(term_width))

def show_local_status(args: dict, api, course_id, assignment_id) -> None:
    # Get course information
    props = {
        "include[]": ["total_scores", "sections", "assignments", "assignment_groups"],
    }
    course = api.get_course_details(course_id, props)
    if not course:
        print("Course not found.")
        return

    if not assignment_id or args['show_course_details']:
        print(f"=== Course Status ===")
        print(f"Course: {course.get('name')} ({course.get('course_code')})")
        print(f"ID: {course.get('id')}")
        if args['output_json']:
            print("\nJSON Output:")
            print(json.dumps(course, indent=2))

    if not assignment_id:
        return
    else:
        print()
    
    # Assignment details
    assignment = api.get_assignment_details(course_id, assignment_id)
    if not assignment:
        print("Assignment not found.")
        return

    print(f"=== Assignment Status ===")
    print(f"Course: {course.get('name')} ({course.get('course_code')})")
    print(f"Assignment: {assignment.get('name')}")
    print(f"ID: {assignment.get('id')}")
    print(f"Due: {format_date(assignment.get('due_at'))}")
    if assignment.get('lock_at'):
        locked = assignment.get('locked_for_user', False)
        print(f"{'Locked' if locked else 'Locks'}: {format_date(assignment.get('lock_at'))}")
    if assignment.get('unlock_at'):
        print(f"Unlocks: {format_date(assignment.get('unlock_at'))}")
    print(f"Points Possible: {assignment.get('points_possible')}")

    if args['show_grades'] or args['show_comments'] or args['show_all_details']:
        print("\nSubmission and grading details will be implemented later.")

    if args['output_json']:
        output = {
            "course": course,
            "assignment": assignment
        }
        print("\nJSON Output:")
        print(json.dumps(output, indent=2))

