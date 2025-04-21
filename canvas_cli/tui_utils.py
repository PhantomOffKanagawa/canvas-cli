"""
Common utilities for Canvas CLI TUI
Contains shared functionality used by both curses-based and text-based interfaces
"""

from typing import Dict, List, Any, Callable, Optional, Tuple
from datetime import datetime
try:
    import curses
except ImportError:
    import importlib.metadata
    command_name = importlib.metadata.name("canvas-cmd")
    print(f"Curses module not available. This may be due to running in an environment that does not support curses.\nIf on Windows run `pip install {command_name}[windows]` to download windows-curses for tui support.")
    curses = None


class FuzzySearch:
    """Utility class for fuzzy searching"""
    
    @staticmethod
    def score_match(term: str, item: Dict) -> int:
        """Score a fuzzy match between a search term and an item
        
        Args:
            term: Search term
            item: Item to search within
            
        Returns:
            Score of the match (higher is better match), 0 if no match
        """
        # Extract searchable text from the item
        name = item.get('name', '').lower() or item.get('meta_label', '').lower() or item.get('meta_data', '').lower()
        code = item.get('course_code', '').lower() if 'course_code' in item else ''
        desc = item.get('description', '').lower() if 'description' in item else ''
        
        score = 0
        
        # Exact matches get highest score
        if term == name:
            return 100
        if term == code:
            return 90
            
        # Prefix matches get high scores
        if name.startswith(term):
            score = max(score, 80 - len(name) + len(term))
        if code and code.startswith(term):
            score = max(score, 75 - len(code) + len(term))
            
        # Substring matches get good scores
        if term in name:
            score = max(score, 70 - name.index(term))
        if code and term in code:
            score = max(score, 65 - code.index(term))
        if desc and term in desc:
            score = max(score, 60 - desc.index(term))
            
        # Word boundary matches
        words = name.split()
        for i, word in enumerate(words):
            if word.startswith(term):
                score = max(score, 60 - i)
        
        # Fuzzy matching (allowing non-consecutive matches with minor differences)
        name_score = FuzzySearch.fuzzy_contains(name, term)
        code_score = FuzzySearch.fuzzy_contains(code, term) if code else 0
        desc_score = FuzzySearch.fuzzy_contains(desc, term) if desc else 0
        
        score = max(score, name_score, code_score, desc_score)
        return score

    @staticmethod
    def fuzzy_contains(text: str, pattern: str) -> int:
        """Check if text contains pattern in a fuzzy way and return a score
        
        Args:
            text: Text to search within
            pattern: Pattern to search for
            
        Returns:
            Score if pattern is found (higher is better), 0 if not found
        """
        if not text or not pattern:
            return 0

        # Allow for some missing characters (fuzzy matching)
        # We can skip up to a quarter of the pattern length in gaps
        max_missing = max(len(pattern) // 4, 2)
        for allowed_missing in range(1, max_missing + 1):
            i, j = 0, 0
            missing = 0
            first_match = -1
            gaps = 0
            while i < len(text) and j < len(pattern):
                if text[i] == pattern[j]:
                    if first_match == -1:
                        first_match = i
                    j += 1
                else:
                    gaps += 1
                    i += 1
                    continue
                i += 1
            # If not all pattern chars matched, try skipping some
            if j < len(pattern):
                missing = len(pattern) - j
            if missing <= allowed_missing:
                base = 50
                # Calculate score based on the number of gaps and missing characters
                # The more gaps or missing characters, the lower the score
                # Calculate missing character penalty as a ratio of the allowed missing
                penalty = (first_match if first_match != -1 else 0) + gaps + (missing // allowed_missing) * 20
                bonus = max(0, len(pattern) - gaps - missing)
                return base + bonus - penalty

        # No fuzzy match found
        return 0

    @staticmethod
    def filter_and_sort_items(items: List[Dict], search_text: str) -> List[Dict]:
        """Filter and sort items by search text
        
        Args:
            items: List of items to filter and sort
            search_text: Search text to filter by
            
        Returns:
            Filtered and sorted list of items
        """
        if not search_text:
            return items.copy()
            
        # Split search text into terms
        search_terms = search_text.lower().split()
        scored_items = []
        
        for item in items:
            # Calculate match score for this item
            total_score = 0
            all_terms_match = True
            
            for term in search_terms:
                term_score = FuzzySearch.score_match(term, item)
                if term_score > 0:
                    total_score += term_score
                else:
                    all_terms_match = False
                    break
                    
            if all_terms_match:
                scored_items.append((total_score, item))
        
        # Sort by score (descending) and extract items
        scored_items.sort(key=lambda x: x[0], reverse=True)  # Higher scores first
        return [item for _, item in scored_items]

class Formatter:
    """Base formatter class for both UI implementations"""
    
    # Icon constants
    ICON_FAVORITE = "★"
    ICON_SUBMITTED = "✓"
    ICON_PAST_DUE = "⌛"
    ICON_LOCKED = "X"
    ICON_NONE = ""

    # Color pair constants for use in the UI
    COLORS_NORMAL = 1
    COLORS_FAVORITE = 2
    COLORS_SUBMITTED = 3
    COLORS_PAST_DUE = 4
    COLORS_LOCKED = 5
    COLORS_HEADER = 6
    COLORS_COMPLETED = 7
    SELECTED = curses.A_REVERSE

    def setup_colors():
        """Initialize color pairs for the curses interface"""
    
    def __init__(self) -> None:
        """Initialize the formatter"""

        # Initialize curses if provided
        curses.start_color()
        curses.use_default_colors()

        # Define color pairs
        curses.init_pair(self.COLORS_NORMAL, curses.COLOR_WHITE, -1)
        curses.init_pair(self.COLORS_FAVORITE, curses.COLOR_YELLOW, -1)
        curses.init_pair(self.COLORS_SUBMITTED, curses.COLOR_GREEN, -1)
        curses.init_pair(self.COLORS_PAST_DUE, curses.COLOR_RED, -1)
        curses.init_pair(self.COLORS_LOCKED, curses.COLOR_MAGENTA, -1)
        curses.init_pair(self.COLORS_HEADER, curses.COLOR_CYAN, -1)
        curses.init_pair(self.COLORS_COMPLETED, curses.COLOR_BLACK, -1)

    @staticmethod
    def format_item(item, type) -> str:
        """Format an item for display"""

        # Determine and display icons based on item status
        i = 0
        now = datetime.now().isoformat()
        due_at = item.get('due_at')
        status = {
            'favorite': item.get('is_favorite', False),
            'submitted': item.get('has_submitted_submissions', False),
            'locked': item.get('locked_for_user', False),
            'past_due': due_at and due_at < now
        }
        icons = []
        # icon_colors = []
        if status['favorite']:
            icons.append(Formatter.ICON_FAVORITE)
            # icon_colors.append(Formatter.COLORS_FAVORITE)
        if status['submitted']:
            icons.append(Formatter.ICON_SUBMITTED)
            # icon_colors.append(Formatter.COLORS_SUBMITTED)
        if status['locked']:
            icons.append(Formatter.ICON_LOCKED)
            # icon_colors.append(Formatter.COLORS_LOCKED)
        if status['past_due']:
            icons.append(Formatter.ICON_PAST_DUE)
            # icon_colors.append(Formatter.COLORS_PAST_DUE)

        string = " ".join(icons) + (" " if icons else "")

        if type == 'assignments':
            name = item.get("name", "Unnamed Assignment")
            due_text = f"Due: {due_at.split('T')[0]}" if due_at else "No due date"
            string = f"{string} {name} ({due_text})"
        else:
            name = item.get('name', 'Unnamed Course')
            code = item.get('course_code', '')
            string = f"{string} {name} ({code})"

        return string

    @staticmethod
    def write_item(stdscr, y, x, width, item, type, selected) -> str:
        """Write a course to the output
        
        Args:
            course: Course dictionary
            
        Returns:
            Formatted string representation of the course
        """

        # Determine and display icons based on item status
        string = Formatter.format_item(item, type)

        if len(string) > width - 4:
            string = string[:width - 7] + "..."

        stdscr.addstr(y, x, string.ljust(width - 2))

    @staticmethod
    def get_color(item: Dict[str, bool]) -> int:
        """Get the color pair for a status
        
        Args:
            item: Dictionary of status flags
            
        Returns:
            Color pair number
        """
        now = datetime.now().isoformat()
        due_at = item.get('due_at')

        if item.get('locked_for_user', False):
            return Formatter.COLORS_LOCKED
        if due_at and due_at < now and item.get('has_submitted_submissions', False):
            return Formatter.COLORS_COMPLETED
        if due_at and due_at < now:
            return Formatter.COLORS_PAST_DUE
        if item.get('has_submitted_submissions', False):
            return Formatter.COLORS_SUBMITTED
        if item.get('is_favorite', False):
            return Formatter.COLORS_FAVORITE
        
        return Formatter.COLORS_NORMAL