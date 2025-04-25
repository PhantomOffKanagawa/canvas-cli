import typer
from typer import Typer, Argument, Option
from typing import Optional
from canvas_cli.handler_helper import echo
from handlers.pull_handler import handle_pull


pull_app = Typer(
    invoke_without_command=True,
    no_args_is_help=False,
    help="Pull a submission file from Canvas LMS",
)

@pull_app.callback()
def pull(
    ctx: typer.Context,
    # ─────────────────────
    # Course and Assignment Identification
    # ─────────────────────
    course_id: int = typer.Option(None, "--course-id", "-cid", help="[Identification] Canvas Course ID."),
    assignment_id: int = typer.Option(None, "--assignment-id", "-aid", help="[Identification] Canvas Assignment ID."),

    # ─────────────────────
    # Output Options
    # ─────────────────────
    output_dir: str = typer.Option(".", "--output-dir", "-od", help="[Output] Directory for output."),
    force: bool = typer.Option(False, "--force", "-f", help="[Output] Overwrite existing files."),

    # ─────────────────────
    # Selection Options
    # ─────────────────────
    submission_number: int = typer.Option(None, "--submission-number", "-sn", help="[Selection] Canvas Submission ID."),
):
    """
    Download assignment details from Canvas.

    Options are grouped by:
    - Course and Assignment Identification
    - Output Options
    - Selection Options
    """
    # If you need to call handle_push, ensure you provide all required parameters
    handle_pull(ctx=ctx, course_id=course_id, assignment_id=assignment_id, output_dir=output_dir)