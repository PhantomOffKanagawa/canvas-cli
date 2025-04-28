import pytest
from unittest.mock import MagicMock, patch
import curses
from canvas_cli.tui import ListSelector, fuzzy_filter

class TestFuzzyFilter:
    def test_fuzzy_filter_basic(self):
        """Test basic fuzzy filtering functionality"""
        items = ["Apple", "Banana", "Cherry", "Date"]
        
        # Test exact match
        assert fuzzy_filter(items, "Apple") == ["Apple"]
        
        # Test fuzzy match (letters in order but not consecutive)
        assert fuzzy_filter(items, "Ape") == ["Apple"]
        assert fuzzy_filter(items, "ana") == ["Banana"]
        
        # Test case insensitivity
        assert fuzzy_filter(items, "cherry") == ["Cherry"]
        
        # Test empty query returns all items
        assert fuzzy_filter(items, "") == items
        
        # Test no matches
        assert fuzzy_filter(items, "xyz") == []
    
    def test_fuzzy_filter_with_key(self):
        """Test fuzzy filtering with a key function"""
        items = [
            {"name": "Apple", "id": 1},
            {"name": "Banana", "id": 2},
            {"name": "Cherry", "id": 3}
        ]
        key = lambda x: x["name"]
        
        # Test with key function
        assert fuzzy_filter(items, "ana", key) == [{"name": "Banana", "id": 2}]
        
        # Test case insensitivity with key
        assert fuzzy_filter(items, "APPLE", key) == [{"name": "Apple", "id": 1}]

class TestListSelector:
    @pytest.fixture
    def mock_stdscr(self):
        """Create a mock curses screen for testing"""
        mock = MagicMock()
        # Set screen size
        mock.getmaxyx.return_value = (25, 80)  # 25 rows, 80 columns
        return mock
        
    def test_initialization(self, mock_stdscr):
        """Test that ListSelector initializes with correct values"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title")
        
        assert selector.stdscr == mock_stdscr
        assert selector.items == items
        assert selector.title == "Test Title"
        assert selector.selected == 0
        assert selector.query == ''
        assert selector.filtered == items
        assert not selector.mouse
        assert selector.top == 0
        assert selector.hovered is None
        assert selector.columns is None
        assert not selector.allow_escape_back
        
    def test_row_offset_property(self, mock_stdscr):
        """Test row_offset property returns correct values based on columns"""
        # Without columns
        selector = ListSelector(mock_stdscr, ["Item"], "Test", columns=None)
        assert selector.row_offset == 2
        
        # With columns
        selector = ListSelector(mock_stdscr, ["Item"], "Test", columns=[("Col", lambda x: x, 10)])
        assert selector.row_offset == 3
        
    def test_max_items_property(self, mock_stdscr):
        """Test max_items property returns correct values based on screen size"""
        # Without columns
        selector = ListSelector(mock_stdscr, ["Item"], "Test", columns=None)
        # 25 (screen height) - 3 = 22
        assert selector.max_items == 22
        
        # With columns
        selector = ListSelector(mock_stdscr, ["Item"], "Test", columns=[("Col", lambda x: x, 10)])
        # 25 (screen height) - 4 = 21
        assert selector.max_items == 21
        
    def test_draw(self, mock_stdscr):
        """Test draw method calls expected curses methods"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title")
        
        selector.draw()
        
        # Verify the expected calls
        mock_stdscr.clear.assert_called_once()
        mock_stdscr.refresh.assert_called_once()
        # Check that addstr was called for title, search bar, and each item
        assert mock_stdscr.addstr.call_count >= 5  # Title + search + 3 items
        
    def test_handle_mouse_hover(self, mock_stdscr):
        """Test mouse hover functionality"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title", mouse=True)
        
        # Simulate mouse hover on the first item (Y = row_offset)
        event = (0, selector.row_offset, 0, 0, 0)  # id, y, x, z, bstate
        result = selector.handle_mouse(event)
        
        assert not result  # Should return False for hover
        assert selector.hovered == 0  # First item
        
    def test_handle_mouse_click(self, mock_stdscr):
        """Test mouse click selection"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title", mouse=True)
        
        # Simulate mouse click on the second item
        event = (0, selector.row_offset + 1, 0, 0, curses.BUTTON1_CLICKED)
        result = selector.handle_mouse(event)
        
        assert result  # Should return True for click
        assert selector.selected == 1  # Second item
        assert selector.hovered == 1
        
    @patch('curses.curs_set')
    def test_run_keyboard_navigation(self, mock_curs_set, mock_stdscr):
        """Test keyboard navigation in run method"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title")
        
        # Setup key sequence: DOWN, DOWN, ENTER
        mock_stdscr.getch.side_effect = [
            curses.KEY_DOWN,
            curses.KEY_DOWN,
            10  # ENTER
        ]
        
        result = selector.run()
        
        assert result == "Item 3"  # Third item selected after two downs
        assert selector.selected == 2
        
    @patch('curses.curs_set')
    def test_run_escape_normal(self, mock_curs_set, mock_stdscr):
        """Test ESC behavior with allow_escape_back=False"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title")
        
        # Press ESC
        mock_stdscr.getch.return_value = 27  # ESC
        
        result = selector.run()
        
        assert result is None
        
    @patch('curses.curs_set')
    def test_run_escape_with_back(self, mock_curs_set, mock_stdscr):
        """Test ESC behavior with allow_escape_back=True"""
        items = ["Item 1", "Item 2", "Item 3"]
        selector = ListSelector(mock_stdscr, items, "Test Title", allow_escape_back=True)
        
        # Press ESC
        mock_stdscr.getch.side_effect = [27]  # ESC
        
        result = selector.run()
        
        assert result == "__ESCAPE__"
        
    @patch('curses.curs_set')
    def test_run_backspace(self, mock_curs_set, mock_stdscr):
        """Test backspace handling in search"""
        items = ["Apple", "Banana", "Cherry"]
        selector = ListSelector(mock_stdscr, items, "Test Title")
        
        # Type 'ab', then backspace, then ENTER
        mock_stdscr.getch.side_effect = [ord('a'), ord('b'), curses.KEY_BACKSPACE, 10]
        
        result = selector.run()
        
        assert selector.query == 'a'
        assert result == "Apple"  # First match should be selected