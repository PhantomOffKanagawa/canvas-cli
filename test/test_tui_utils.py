import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from canvas_cli.tui_utils import EmojiIcons

@pytest.fixture
def mock_emoji_level_0():
    with patch('canvas_cli.tui_utils.get_emoji_level', return_value=0):
        yield

@pytest.fixture
def mock_emoji_level_1():
    with patch('canvas_cli.tui_utils.get_emoji_level', return_value=1):
        yield

@pytest.fixture
def mock_emoji_level_2():
    with patch('canvas_cli.tui_utils.get_emoji_level', return_value=2):
        yield

def test_emoji_icons_level_0(mock_emoji_level_0):
    icons = EmojiIcons()
    assert icons.folder == "DIR"
    assert icons.file == "F"
    assert icons.check == "Y"
    assert icons.cross == "N"
    assert icons.star == "*"
    assert icons.dot_green == "."
    assert icons.dot_white == "."
    assert icons.medal == "G"

def test_emoji_icons_level_1(mock_emoji_level_1):
    icons = EmojiIcons()
    assert icons.folder == "DIR"
    assert icons.file == "F"
    assert icons.check == "✔"
    assert icons.cross == "✗"
    assert icons.star == "*"
    assert icons.dot_green == "O"
    assert icons.dot_white == "."
    assert icons.medal == "G"

def test_emoji_icons_level_2(mock_emoji_level_2):
    icons = EmojiIcons()
    assert icons.folder == "📁"
    assert icons.file == "📄"
    assert icons.check == "✔"
    assert icons.cross == "✗"
    assert icons.star == "★"
    assert icons.dot_green == "🟢"
    assert icons.dot_white == "⚪"
    assert icons.medal == "🏅"

def test_dot_method():
    icons = EmojiIcons()
    assert icons.dot('green') == icons.dot_green
    assert icons.dot('anything_else') == icons.dot_white

def test_course_icon():
    icons = EmojiIcons()
    # Test available favorite course
    course1 = {"workflow_state": "available", "is_favorite": True}
    assert icons.course_icon(course1) == f"{icons.star} {icons.dot_green} "
    
    # Test non-available, non-favorite course
    course2 = {"workflow_state": "not_available", "is_favorite": False}
    assert icons.course_icon(course2) == f"  {icons.dot_white} "

def test_assignment_icon():
    icons = EmojiIcons()
    
    # Test submitted assignment
    assignment1 = {"has_submitted_submissions": True, "graded": False}
    assert icons.assignment_icon(assignment1) == f"{icons.check} "
    
    # Test late/missing assignment
    now = datetime.now()
    past = (now - timedelta(days=1)).isoformat()
    assignment2 = {"has_submitted_submissions": False, "due_at": past}
    assert icons.assignment_icon(assignment2) == f"{icons.cross} "
    
    # Test upcoming assignment
    future = (now + timedelta(days=1)).isoformat()
    assignment3 = {"has_submitted_submissions": False, "due_at": future}
    assert icons.assignment_icon(assignment3) == "  "
    
    # Test graded assignment
    assignment4 = {"has_submitted_submissions": True, "graded": True}
    assert icons.assignment_icon(assignment4) == f"{icons.check} {icons.medal} "

def test_format_course():
    icons = EmojiIcons()
    course = {"name": "Test Course", "workflow_state": "available", "is_favorite": True}
    expected = f"{icons.star} {icons.dot_green} Test Course"
    assert icons.format_course(course) == expected

def test_format_assignment():
    icons = EmojiIcons()
    assignment = {"name": "Test Assignment", "has_submitted_submissions": True, "graded": False}
    expected = f"{icons.check} Test Assignment"
    assert icons.format_assignment(assignment) == expected