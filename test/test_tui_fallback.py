import pytest
from unittest.mock import patch, MagicMock
from canvas_cli.tui_fallback import fallback_tui

def test_fallback_tui_no_courses():
    result = fallback_tui([])
    assert result == (None, None, None)

def test_fallback_tui_single_course():
    course = {"name": "Math 101"}
    result = fallback_tui([course])
    assert result == (course, None, None)

@patch('builtins.input', return_value="1")
def test_fallback_tui_multiple_courses(mock_input):
    courses = [
        {"name": "Math 101", "is_favorite": True},
        {"name": "Physics 101"}
    ]
    ctx = MagicMock()
    
    with patch('canvas_cli.tui_fallback.echo') as mock_echo:
        result = fallback_tui(courses, ctx=ctx)
    
        assert result == (courses[0], None, None)
        mock_input.assert_called_once()
        mock_echo.assert_called()

@patch('builtins.input', side_effect=["invalid", "2"])
def test_fallback_tui_invalid_course_selection(mock_input):
    courses = [{"name": "Math 101"}, {"name": "Physics 101"}]
    ctx = MagicMock()
    
    result = fallback_tui(courses, ctx=ctx)
    
    assert result == (courses[1], None, None)
    assert mock_input.call_count == 2

def test_fallback_tui_single_assignment():
    course = {"name": "Math 101"}
    assignment = {"name": "Homework 1"}
    
    result = fallback_tui([course], [assignment])
    
    assert result == (course, assignment, None)

@patch('builtins.input', return_value="1")
def test_fallback_tui_multiple_assignments(mock_input):
    course = {"name": "Math 101"}
    assignments = [
        {"name": "Homework 1", "due_at": "2023-01-01"},
        {"name": "Homework 2", "due_at": None}
    ]
    
    result = fallback_tui([course], assignments)
    
    assert result == (course, assignments[0], None)
    mock_input.assert_called_once()

@patch('builtins.input', side_effect=["1", "2"])
def test_fallback_tui_course_and_assignment_selection(mock_input):
    courses = [{"name": "Math 101"}, {"name": "Physics 101"}]
    assignments = [{"name": "Homework 1"}, {"name": "Homework 2"}]
    
    result = fallback_tui(courses, assignments)
    
    assert result == (courses[0], assignments[1], None)
    assert mock_input.call_count == 2

def test_fallback_tui_single_file():
    course = {"name": "Math 101"}
    assignment = {"name": "Homework 1"}
    files = ["report.pdf"]
    
    result = fallback_tui([course], [assignment], files)
    
    assert result == (course, assignment, files[0])

@patch('builtins.input', return_value="1")
def test_fallback_tui_multiple_files(mock_input):
    course = {"name": "Math 101"}
    assignment = {"name": "Homework 1"}
    files = ["report.pdf", "data.csv"]
    
    result = fallback_tui([course], [assignment], files)
    
    assert result == (course, assignment, files[0])
    mock_input.assert_called_once()

@patch('builtins.input', return_value="q")
def test_fallback_tui_skip_file(mock_input):
    course = {"name": "Math 101"}
    assignment = {"name": "Homework 1"}
    files = ["report.pdf", "data.csv"]
    
    result = fallback_tui([course], [assignment], files)
    
    assert result == (course, assignment, None)
    mock_input.assert_called_once()