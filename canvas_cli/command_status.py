"""
Helper functions for the Canvas CLI status command
Handles displaying the global or local status of courses and grades.
"""

import json
from math import ceil
import random

from canvas_cli.api import format_date
import shutil
from html import unescape
import re

def show_global_status(api, args):
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

    if args.json:
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

    if term_width < 120 or not args.messages:
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

            if sizes['messages'] > 0:
                trimmed_message = message[:sizes['messages']]
                print(f"{nickname:<{sizes['course']}} │ {grade_text:>{sizes['grade'] + len(grade_color) + len(reset_color)}} │ {bar} │ {trimmed_message}")
            else:
                print(f"{nickname:<{sizes['course']}} │ {grade_text:>{sizes['grade'] + len(grade_color) + len(reset_color)}} │ {bar}")

        else:
            reset_color = '\033[0m'
            grade_text = f"\033[90mN/A{reset_color}"
            bar = f"\033[90m{' ' * sizes['progress']}{reset_color}"
            message = "No enrollment data"


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
    
    all = args.all

    if not assignment_id or args.course_details:
        # Course details
        print(f"=== Course Status ===")
        print(f"Course: {course.get('name')} ({course.get('course_code')})")
        print(f"Course ID: {course.get('id')}")

        if all:
            print(f"Locale: {course.get('locale', 'N/A')}, Time Zone: {course.get('time_zone', 'N/A')}")
            print(f"Created: {format_date(course.get('created_at'))}")
            print(f"Sections:")
            for section in course.get('sections', []):
                print(f"  - {section.get('name')} (ID: {section.get('id')}, Role: {section.get('enrollment_role')})")
        enrollments = course.get('enrollments', [])
        if enrollments:
            enrollment = enrollments[0]
            if all:
                print(f"Enrollment: {enrollment.get('role')} (State: {enrollment.get('enrollment_state')})")
            print(f"Current Grade: {enrollment.get('computed_current_grade')} ({enrollment.get('computed_current_score')}%)")
            print(f"Final Grade: {enrollment.get('computed_final_grade')} ({enrollment.get('computed_final_score')}%)")
        
        if all:
            print(f"Public: {course.get('is_public')}, Workflow State: {course.get('workflow_state')}")
            print(f"Storage Quota: {course.get('storage_quota_mb')} MB")
            print(f"Apply Assignment Group Weights: {course.get('apply_assignment_group_weights')}")
        
        print()
        if args.json:
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

    # Assignment details
    print(f"=== Assignment Status ===")
    print(f"Course: {course.get('name')} ({course.get('course_code')})")
    print(f"Assignment: {assignment.get('name')} (ID: {assignment.get('id')})")
    print(f"URL: {assignment.get('html_url')}")
    print(f"Status: {assignment.get('workflow_state').capitalize()}")
    print(f"Points Possible: {assignment.get('points_possible')}")
    
    if all:
        print(f"Grading Type: {assignment.get('grading_type')}")
        print(f"Assignment Group ID: {assignment.get('assignment_group_id')}")
        print(f"Created: {format_date(assignment.get('created_at'))}")
        print(f"Updated: {format_date(assignment.get('updated_at'))}")
    print(f"Due: {format_date(assignment.get('due_at'))}")
    if assignment.get('lock_at'):
        locked = assignment.get('locked_for_user', False)
        print(f"{'Locked' if locked else 'Locks'}: {format_date(assignment.get('lock_at'))}")
    if assignment.get('unlock_at'):
        print(f"Unlocks: {format_date(assignment.get('unlock_at'))}")
    print(f"Published: {'Yes' if assignment.get('published') else 'No'}")
    print(f"Submission Types: {', '.join(assignment.get('submission_types', []))}")
    
    if all:
        print(f"Peer Reviews: {'Yes' if assignment.get('peer_reviews') else 'No'}")
        print(f"Anonymous Grading: {'Yes' if assignment.get('anonymous_grading') else 'No'}")
        print(f"Visible to Everyone: {'Yes' if assignment.get('visible_to_everyone') else 'No'}")
    
    print(f"Rubric Used: {'Yes' if assignment.get('use_rubric_for_grading') else 'No'}")
    if assignment.get('rubric'):
        print(f"Rubric: {assignment['rubric_settings'].get('title', 'Untitled')}")
        for idx, criterion in enumerate(assignment['rubric'], 1):
            print(f"  {idx}. {criterion.get('description')} ({criterion.get('points')} pts)")
    
    if all:
        if assignment.get('description'):
            desc = assignment['description']
            desc = re.sub('<[^<]+?>', '', desc)  # Strip HTML tags
            desc = unescape(desc).strip()
            if desc:
                print("\nDescription:")
                print(desc)

    # Submission details
    submission = assignment.get('submission')
    if submission:
        print("\n=== Submission Status ===")
        print(f"Submitted: {'Yes' if submission.get('submitted_at') else 'No'}")
        if submission.get('submitted_at'):
            print(f"Submitted At: {format_date(submission.get('submitted_at'))}")
        
        if all:
            print(f"Score: {submission.get('score')}")        

        if submission.get('grade'):
            print(f"Grade: {submission.get('grade')} / {assignment.get('points_possible')}")
            print(f"Grade Percentage: {submission.get('grade') / assignment.get('points_possible') * 100:.2f}%")
        
        if all:
            print(f"Attempt: {submission.get('attempt')}")
            print(f"Workflow State: {submission.get('workflow_state')}")
            print(f"Late: {'Yes' if submission.get('late') else 'No'}")
            print(f"Missing: {'Yes' if submission.get('missing') else 'No'}")
        
        if submission.get('attachments'):
            print("Attachments:")
            for att in submission['attachments']:
                print(f"  - {att.get('display_name')} ({att.get('size', 0)//1024} KB): {att.get('url')}")
        
        if all:
            if submission.get('preview_url'):
                print(f"Preview URL: {submission.get('preview_url')}")
            if submission.get('graded_at'):
                print(f"Graded At: {format_date(submission.get('graded_at'))}")
            if submission.get('posted_at'):
                print(f"Posted At: {format_date(submission.get('posted_at'))}")
            if submission.get('excused'):
                print("Excused: Yes")
        if submission.get('points_deducted') is not None:
            print(f"Points Deducted: {submission.get('points_deducted')}")
        if submission.get('redo_request'):
            print("Redo Requested: Yes")
    else:
        print("\nNo submission found for this assignment.")

    # Score statistics
    stats = assignment.get('score_statistics')
    if stats:
        print("\n=== Score Statistics ===")
        print(f"Min: {stats.get('min')}, Max: {stats.get('max')}, Mean: {stats.get('mean')}")
        print(f"Median: {stats.get('median')}, Lower Q: {stats.get('lower_q')}, Upper Q: {stats.get('upper_q')}")

    if args.json:
        output = {
            "course": course,
            "assignment": assignment
        }
        print("\nJSON Output:")
        print(json.dumps(output, indent=2))

