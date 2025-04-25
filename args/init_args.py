import typer
from typer import Typer, Argument, Option
from typing import Optional
from handlers.init_handler import init_handler

init_app = Typer(
    invoke_without_command=True,
    no_args_is_help=False,
    help="Initialize folder with information",
)

@init_app.callback()
def pull_callback(
    ctx: typer.Context,
    course_id: Optional[int] = Option(
        None, "--course_id", "-cid", help="Course ID"
    ),
    assignment_id: Optional[int] = Option(
        None, "--assignment_id", "-aid", help="Assignment ID"
    ),
    file: Optional[str] = Option(
        None, "--file", "-f", help="Path to the file to be submitted"
    ),
):
    """Initialize a folder with the course and assignment ID"""
    init_handler(
        ctx=ctx,
        course_id=course_id,
        assignment_id=assignment_id,
        file=file,
    )