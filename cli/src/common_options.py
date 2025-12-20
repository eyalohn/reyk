import typer

from .consts import DEFAULT_LIBS_DEP_GROUP, DEFAULT_LIBS_PATH

option_group = typer.Option(
    default=DEFAULT_LIBS_DEP_GROUP,
    help="Dependency group to to vendor.",
)
option_libs_path = typer.Option(
    default=DEFAULT_LIBS_PATH,
    help="Directory to vendor the dependencies into.",
)
