import typer
from typer import Typer, Argument, Option
from typing import Optional
from canvas_cli.handler_helper import echo
from handlers.push_handler import handle_push


push_app = Typer(
    invoke_without_command=True,
    no_args_is_help=False,
    help="Push a file to Canvas LMS",
)

@push_app.callback()
def push_callback(
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
    """Submit an assignment to Canvas"""
    handle_push(
        ctx=ctx,
        course_id=course_id,
        assignment_id=assignment_id,
        file=file,
    )