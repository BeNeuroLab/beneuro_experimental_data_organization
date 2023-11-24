from typing_extensions import Annotated
import datetime

import typer
from rich import print

from beneuro_data.query_sessions import list_all_sessions_on_day
from beneuro_data.config import _load_config


def list_today(
    processing_level: Annotated[
        str,
        typer.Argument(help="Processing level of the session. raw or processed."),
    ] = "raw",
    check_locally: Annotated[
        bool,
        typer.Option("--local/--remote", help="Check local or remote data."),
    ] = True,
) -> list[tuple[str, str]]:
    """
    List all sessions of all subjects that happened today.
    """
    if processing_level not in ["raw", "processed"]:
        raise ValueError("Processing level must be raw or processed.")

    config = _load_config()
    root_path = config.LOCAL_PATH if check_locally else config.REMOTE_PATH

    raw_or_processed_path = root_path / processing_level
    if not raw_or_processed_path.exists():
        raise FileNotFoundError(f"{raw_or_processed_path} found.")

    today = datetime.datetime.today()

    todays_sessions_with_subject = list_all_sessions_on_day(
        raw_or_processed_path, today, config.IGNORED_SUBJECT_LEVEL_DIRS
    )

    for subj, sess in todays_sessions_with_subject:
        print(f"{subj} - {sess}")
