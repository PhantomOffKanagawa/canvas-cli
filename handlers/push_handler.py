from functools import wraps
import typer
from typing import Any, Optional
import json
import os
from pathlib import Path
from canvas_cli.handler_helper import echo
from handlers.config_handler import get_key

# ──────────────────────
# HANDLER FUNCTIONS
# ──────────────────────

def handle_push(ctx: typer.Context, course_id: Optional[int], assignment_id: Optional[int], file: Optional[str]):
    """Push a file to an assignment in Canvas LMS"""
    
    course_id = get_key("course_id", ctx)
    assignment_id = get_key("assignment_id", ctx)
    file = get_key("file", ctx)
    
    echo(f"Course ID: {course_id}", ctx=ctx)
    echo(f"Assignment ID: {assignment_id}", ctx=ctx)
    echo(f"File: {file}", ctx=ctx)