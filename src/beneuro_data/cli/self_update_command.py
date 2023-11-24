from typing_extensions import Annotated
import typer

from beneuro_data.update_bnd import update_bnd


def self_update(
    verbose: Annotated[
        bool,
        typer.Option(help="Print new commits that were pulled."),
    ] = True,
):
    """
    Update the bnd tool by pulling the latest commits from the repo's main branch.
    """
    update_bnd(print_new_commits=verbose)
