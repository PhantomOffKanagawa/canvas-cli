from functools import wraps
import typer
from typing import Any, Optional
import json
import os
from pathlib import Path
from canvas_cli.handler_helper import echo, get_api
from handlers.config_handler import get_key
from canvas_cli.api import CanvasAPI
from canvas_cli.tui import run_tui


# ──────────────────────
# HANDLER FUNCTIONS
# ──────────────────────

def handle_push(ctx: typer.Context, course_id: Optional[int], assignment_id: Optional[int], file: Optional[str], tui: bool = False):
    """Push a file to an assignment in Canvas LMS, optionally using TUI"""
    if tui:
        out = run_tui(file_select_enabled=True, file_select_escape_behavior="exit", ctx=ctx)
        
        if out is None:
            echo("Exiting...", ctx=ctx)
            raise typer.Abort()
        
        course, assignment, file_path = out
        
        if course is None or assignment is None:
            echo("Exiting...", ctx=ctx)
            raise typer.Abort()
        
        course_id = course.get("id", None)
        assignment_id = assignment.get("id", None)
        
        if file_path:
            file = file_path

    # Get the course_id, assignment_id, and file from the context or configs
    course_id = get_key("course_id", ctx)
    assignment_id = get_key("assignment_id", ctx)
    file = get_key("file", ctx)
    
    # Check if course_id, assignment_id, and file are provided
    if not course_id or not assignment_id:
        echo("Error: Missing course_id, assignment_id.", ctx=ctx, level="error")
        return

    # Check if file is provided
    if not file:
        typer.echo("Error: File path must be provided.")
        return
    
    # Check if the file exists
    if not os.path.exists(file):
        echo(f"Error: File '{file}' does not exist.", ctx=ctx, level="error")
        return
    
    # Get the API instance from the context
    api = get_api(ctx)
    if not api:
        echo("Error: Failed to get API instance.", ctx=ctx, level="error")
        return
    
    # Submit the assignment
    response = api.submit_assignment(course_id, assignment_id, file)