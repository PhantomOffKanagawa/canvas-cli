"""
Tests for the pull command
"""

import sys
from unittest.mock import patch, MagicMock

from test_base import CanvasCliTestCase
from canvas_cli.args import create_parser, parse_args_and_dispatch

class PullTests(CanvasCliTestCase):
    """Tests for the pull command"""
    