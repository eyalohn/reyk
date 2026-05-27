from pathlib import Path
from typing import Annotated, cast

import typer

from reyk_cli.configuration_reader import DEFAULT_VENDOR_GROUP, read_reyk_configuration
from reyk_cli.uv_vendorizer import UVBasedVendorizer

app = typer.Typer(
    help="Manage isolated environment dependencies.",
    no_args_is_help=True,
)

group_option = typer.Option(
    default=DEFAULT_VENDOR_GROUP,
    help="Dependency group to to vendor.",  # https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups
)


@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Path,
        typer.Option(
            help="Where to find pyproject.toml containing vendorized dependencies",
            file_okay=True,
            dir_okay=False,
            exists=True,
            readable=True,
        ),
    ] = Path("./pyproject.toml"),
) -> None:
    reyk_config = read_reyk_configuration(config)
    ctx.obj = UVBasedVendorizer(
        project_root=config.parent,
        vendor_groups=reyk_config.vendor_groups,
        libraries_target_path=Path(reyk_config.libraries_path),
    )


@app.command(help="Vendor the isolated environment dependencies.")
def sync(ctx: typer.Context) -> None:
    """Install the isolated environment dependencies."""
    cast(UVBasedVendorizer, ctx.obj).sync_from_group_to_target_path()


@app.command(
    add_help_option=False,
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def add(
    ctx: typer.Context,
    group: str = group_option,
) -> None:
    """Add packages to the isolated environment."""
    vendorizer = cast(UVBasedVendorizer, ctx.obj)
    vendorizer.add_new_requirement_to_pyproject(group, ctx.args)
    vendorizer.sync_from_group_to_target_path()


@app.command(
    add_help_option=False,
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def remove(
    ctx: typer.Context,
    group: str = group_option,
) -> None:
    """Remove packages from the isolated environment."""
    vendorizer = cast(UVBasedVendorizer, ctx.obj)
    vendorizer.remove_requirement_from_pyproject(group, ctx.args)
    vendorizer.sync_from_group_to_target_path()


if __name__ == "__main__":  # pragma: no cover
    app()
