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

def handle_pull(ctx: typer.Context, course_id: Optional[int], assignment_id: Optional[int], output_dir: Optional[str], tui: bool = False):
    """Pull a file from an assignment in Canvas LMS, optionally using TUI"""
    if tui:
        out = run_tui(file_select_enabled=False)
        
        if out is None:
            echo("Exiting...", ctx=ctx)
            raise typer.Abort()
        
        course, assignment, _ = out
        course_id = course.get("id", None)
        assignment_id = assignment.get("id", None)
    
    # ──────────────────────
    # INITIALIZATION
    # ──────────────────────
    
    # Get the course_id, assignment_id, and file from the context or configs
    course_id = get_key("course_id", ctx)
    assignment_id = get_key("assignment_id", ctx)
    
    # Check if course_id, assignment_id, and file are provided
    if not course_id or not assignment_id:
        echo("Error: Missing course_id, assignment_id", ctx=ctx, level="error")
        return

    # Get the API instance from the context
    api = get_api(ctx)
    if not api:
        echo("Error: Failed to get API instance", ctx=ctx, level="error")
        return
    
    # Check if output_dir is provided
    if not output_dir:
        output_dir = os.getcwd()  # Default to current working directory
    else:
        # Check if the path exists and is a file
        if os.path.exists(output_dir) and not os.path.isdir(output_dir):
            echo(f"Error: '{output_dir}' is not a valid directory", ctx=ctx, level="error")
            raise typer.Exit(code=1)

        # Try to create the directory
        try:
            os.makedirs(output_dir, exist_ok=True)
        except FileExistsError:
            echo(f"Error: '{output_dir}' exists but cannot be used as a directory", ctx=ctx, level="error")
            raise typer.Exit(code=1)
        
    # ──────────────────────
    # HANDLE PULL LOGIC
    # ──────────────────────
        
    # Get the assignment submissions
    submissions_response = api.get_submissions(course_id, assignment_id)
    if not submissions_response:
        echo("Error: No submissions found", ctx=ctx, level="error")
        return
    
    # Get the submissions from the response
    submissions = submissions_response.get("submission_history", None)

    if not submissions or len(submissions) == 0:
        echo("Error: No submissions found", ctx=ctx, level="error")
        return
    
    # Check if there is one submission
    if len(submissions) == 1:
        submission = submissions[0]
        echo(f"Found one submission: {submission['id']}", ctx=ctx, level="debug")
    else:
        # If multiple submissions, check if submission_number is provided
        submission_number = len(submissions)
        
        # Try to get the wanted submission from the params
        wanted_submission = ctx.params.get('submission_number', None)
        
        if wanted_submission is None:
            # List all submissions
            points_possible = submissions_response.get("assignment", {}).get("points_possible", None)
            echo("Multiple submissions found. Please select one:", ctx=ctx, level="info")
            for index, submission in enumerate(submissions, start=1):
                submitted_at = submission.get("submitted_at", None)
                submission_type = submission.get("submission_type", None)
                score = submission.get("score", None) or submission.get("points", None)
                display_name = ", ".join([attach.get("display_name", None) for attach in submission.get("attachments", None)])
                echo(f"Submission {index}{' - ' + api.format_date(submitted_at) if submitted_at else ''}{' - ' + submission_type if submission_type else ''}{' - ' + score + '/' + points_possible if score and points_possible else ''}{' - ' + display_name if display_name else ' - No Display Name'}", ctx=ctx, level="info")
            
            
            # Prompt the user for the submission number
            while wanted_submission is None:
                try:
                    # Prompt for submission number
                    input_value = typer.prompt(f"Please enter the submission number (1-{submission_number}) or q to quit: ")
                    
                    # Check if user wants to quit
                    if input_value.lower() == "q":
                        echo("Exiting...", ctx=ctx, level="info")
                        raise typer.Exit(code=0)
                    
                    # Try to convert to int
                    wanted_submission = int(input_value)
                    if wanted_submission < -(submission_number - 1) or wanted_submission > submission_number:
                        echo(f"Error: Submission number must be between {-(submission_number - 1)} and {submission_number}", ctx=ctx, level="error")
                        wanted_submission = None
                except ValueError:
                    echo("Error: Invalid input. Please enter a valid submission number", ctx=ctx, level="error")
                    wanted_submission = None
        
        if wanted_submission < -(submission_number - 1) or wanted_submission > submission_number:
            echo(f"Error: Submission number must be between {-(submission_number - 1)} and {submission_number}", ctx=ctx, level="error")
            raise typer.Exit(code=1)
            
        # Get the selected submission
        if wanted_submission < 0:
            # If the user entered a negative number, get the submission from the end
            wanted_submission = submission_number + wanted_submission
            
        # Selected number is 1 based so we need to subtract 1
        submission = submissions[wanted_submission - 1]
        display_name = ", ".join([attach.get("display_name", None) for attach in submission.get("attachments", None)])
        echo(f"Selected submission: {wanted_submission} - Display Name: {display_name}", ctx=ctx, level="debug")
        
        # Triple check if the submission is valid
        if not submission:
            echo(f"Error: Submission number {submission_number} not found", ctx=ctx, level="error")
            raise typer.Exit(code=1)
            
    # Get the file name from the submission
    file_name = submission.get("filename", "submission_file")
    file_path = os.path.join(output_dir, file_name)
    
    # Download the file(s)
    attachments = submission.get("attachments", None)
    download_count = 0
    if attachments:
        for attach in attachments:
            response = api.download_file(attach.get("url", None), os.path.join(output_dir, attach.get("filename", None)), overwrite=ctx.params.get('force', False))
            if response:
                echo(f"Downloaded {attach.get('filename', None)} to {output_dir}", ctx=ctx)
                download_count += 1
        if download_count != 0:  
            echo(f"Downloaded {len(attachments)} attachments from the latest submission to {output_dir}", ctx=ctx)
    return

