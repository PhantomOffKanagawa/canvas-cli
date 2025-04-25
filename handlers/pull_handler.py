from functools import wraps
import typer
from typing import Any, Optional
import json
import os
from pathlib import Path
from canvas_cli.handler_helper import echo, get_api
from handlers.config_handler import get_key
from canvas_cli.api import CanvasAPI


# ──────────────────────
# HANDLER FUNCTIONS
# ──────────────────────

def handle_pull(ctx: typer.Context, course_id: Optional[int], assignment_id: Optional[int], output_dir: Optional[str]):
    """Pull a file from an assignment in Canvas LMS"""
    
    # ──────────────────────
    # INITIALIZATION
    # ──────────────────────
    
    # Get the course_id, assignment_id, and file from the context or configs
    course_id = get_key("course_id", ctx)
    assignment_id = get_key("assignment_id", ctx)
    
    # Check if course_id, assignment_id, and file are provided
    if not course_id or not assignment_id:
        echo("Error: Missing course_id, assignment_id.", ctx=ctx, level="error")
        return

    # Get the API instance from the context
    api = get_api(ctx)
    if not api:
        echo("Error: Failed to get API instance.", ctx=ctx, level="error")
        return
    
    # Check if output_dir is provided
    if not output_dir:
        output_dir = os.getcwd()  # Default to current working directory
    else:
        # Check if the path exists and is a file
        if os.path.exists(output_dir) and not os.path.isdir(output_dir):
            echo(f"Error: '{output_dir}' is not a valid directory.", ctx=ctx, level="error")
            raise typer.Exit(code=1)

        # Try to create the directory
        try:
            os.makedirs(output_dir, exist_ok=True)
        except FileExistsError:
            echo(f"Error: '{output_dir}' exists but cannot be used as a directory.", ctx=ctx, level="error")
            raise typer.Exit(code=1)
        
    # ──────────────────────
    # HANDLE PULL LOGIC
    # ──────────────────────
        
    # Get the assignment submissions
    submissions_response = api.get_submissions(course_id, assignment_id)
    if not submissions_response:
        echo("Error: No submissions found.", ctx=ctx, level="error")
        return
    
    # Get the submissions from the response
    submissions = submissions_response.get("submission_history", None)

    if not submissions or len(submissions) == 0:
        echo("Error: No submissions found.", ctx=ctx, level="error")
        return
    
    # Check if there is one submission
    if len(submissions) == 1:
        submission = submissions[0]
        echo(f"Found one submission: {submission['id']}", ctx=ctx, level="debug")
    else:
        # If multiple submissions, check if submission_number is provided
        submission_number = len(submissions)
        
        # List all submissions
        points_possible = submissions_response.get("assignment", {}).get("points_possible", None)
        echo("Multiple submissions found. Please select one:", ctx=ctx, level="info")
        for index, submission in enumerate(submissions, start=1):
            submitted_at = submission.get("submitted_at", None)
            submission_type = submission.get("submission_type", None)
            score = submission.get("score", None) or submission.get("points", None)
            display_name = ", ".join([attach.get("display_name", None) for attach in submission.get("attachments", None)])
            echo(f"Submission {index}{' - ' + api.format_date(submitted_at) if submitted_at else ''}{' - ' + submission_type if submission_type else ''}{' - ' + score + '/' + points_possible if score and points_possible else ''}{' - ' + display_name if display_name else ' - No Display Name'}", ctx=ctx, level="info")
        
        # Try to get the wanted submission from the params
        wanted_submission = ctx.params.get('submission_number', None)
        
        # Prompt the user for the submission number
        while wanted_submission is None:
            try:
                # Prompt for submission number try to convert to int
                wanted_submission = int(typer.prompt(f"Please enter the submission number (1-{submission_number}) or q to quit: "))
                if wanted_submission < 1 or wanted_submission > submission_number:
                    echo(f"Error: Submission number must be between 1 and {submission_number}.", ctx=ctx, level="error")
                    wanted_submission = None
            except ValueError:
                # If the user enters 'q', exit the program
                # Else loop
                if wanted_submission == "q":
                    echo("Exiting...", ctx=ctx, level="info")
                    raise typer.Exit(code=0)
                echo("Error: Invalid input. Please enter a valid submission number.", ctx=ctx, level="error")
        
        # Get the selected submission
        # Selected number is 1 based so we need to subtract 1
        submission = submissions[wanted_submission - 1]
        echo(f"Selected submission: {submission['id']}", ctx=ctx, level="debug")
        
        # Tripple check if the submission is valid
        if not submission:
            echo(f"Error: Submission number {submission_number} not found.", ctx=ctx, level="error")
            raise typer.Exit(code=1)
            
    # Get the file name from the submission
    file_name = submission.get("filename", "submission_file")
    file_path = os.path.join(output_dir, file_name)
    
    # Download the file(s)
    attachments = submission.get("attachments", None)
    if attachments:
        for attach in attachments:
            api.download_file(attach.get("url", None), os.path.join(output_dir, attach.get("filename", None)), overwrite=ctx.params.get('force', False))
        print(f"Downloaded {len(attachments)} attachments from the latest submission to {output_dir}.")
    return

