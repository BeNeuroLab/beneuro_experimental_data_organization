from pathlib import Path
from typing_extensions import Annotated
import datetime

import typer
from rich import print

from beneuro_data.query_sessions import (
    get_last_session_path,
    list_subject_sessions_on_day,
)
from beneuro_data.data_validation import validate_raw_session
from beneuro_data.config import _load_config


def validate_today(
    processing_level: Annotated[
        str,
        typer.Argument(help="Processing level of the session. raw or processed."),
    ] = "raw",
    check_locally: Annotated[
        bool,
        typer.Option("--local/--remote", help="Check local or remote data."),
    ] = True,
    check_behavior: Annotated[
        bool,
        typer.Option(
            "--check-behavior/--ignore-behavior", help="Check behavioral data or not."
        ),
    ] = True,
    check_ephys: Annotated[
        bool,
        typer.Option("--check-ephys/--ignore-ephys", help="Check ephys data or not."),
    ] = True,
    check_videos: Annotated[
        bool,
        typer.Option("--check-videos/--ignore-videos", help="Check videos data or not."),
    ] = True,
):
    """
    Validate all sessions of all subjects that happened today.
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not check_behavior, not check_ephys, not check_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()
    root_path = config.LOCAL_PATH if check_locally else config.REMOTE_PATH
    raw_or_processed_path = root_path / processing_level

    today = datetime.datetime.today()

    for subject_path in raw_or_processed_path.iterdir():
        if not subject_path.is_dir():
            continue

        subject_name = subject_path.name
        todays_sessions_with_subject = list_subject_sessions_on_day(subject_path, today)
        for session_name in todays_sessions_with_subject:
            session_path = subject_path / session_name
            try:
                validate_raw_session(
                    session_path,
                    subject_name,
                    check_behavior,
                    check_ephys,
                    check_videos,
                )
            except Exception as e:
                print(f"[bold red]Problem with {session_path.name}: {e.args[0]}\n")
            else:
                print(f"[bold green]{session_path.name} looking good.\n")


def validate_sessions(
    subject_name: Annotated[str, typer.Argument(help="Subject name.")],
    processing_level: Annotated[
        str,
        typer.Argument(help="Processing level of the session. raw or processed."),
    ],
    check_locally: Annotated[
        bool,
        typer.Option("--local/--remote", help="Check local or remote data."),
    ] = True,
    check_behavior: Annotated[
        bool,
        typer.Option(
            "--check-behavior/--ignore-behavior", help="Check behavioral data or not."
        ),
    ] = True,
    check_ephys: Annotated[
        bool,
        typer.Option("--check-ephys/--ignore-ephys", help="Check ephys data or not."),
    ] = True,
    check_videos: Annotated[
        bool,
        typer.Option("--check-videos/--ignore-videos", help="Check videos data or not."),
    ] = True,
):
    """
    Validate (raw) experimental data in all sessions of a given subject.

    See options for which data to check and ignore.
    """

    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not check_behavior, not check_ephys, not check_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()

    root_path = config.LOCAL_PATH if check_locally else config.REMOTE_PATH
    subject_path = root_path / processing_level / subject_name

    for session_path in subject_path.iterdir():
        if session_path.is_dir():
            try:
                validate_raw_session(
                    session_path,
                    subject_name,
                    check_behavior,
                    check_ephys,
                    check_videos,
                )
            except Exception as e:
                print(f"[bold red]Problem with {session_path.name}: {e.args[0]}\n")
            else:
                print(f"[bold green]{session_path.name} looking good.\n")


def validate_session(
    session_path: Annotated[
        Path, typer.Argument(help="Path to session directory. Can be relative or absolute")
    ],
    subject_name: Annotated[
        str,
        typer.Argument(
            help="Name of the subject the session belongs to. (Used for confirmation.)"
        ),
    ],
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session. raw or processed.")
    ] = "raw",
    check_behavior: Annotated[
        bool,
        typer.Option(
            "--check-behavior/--ignore-behavior", help="Check behavioral data or not."
        ),
    ] = True,
    check_ephys: Annotated[
        bool,
        typer.Option("--check-ephys/--ignore-ephys", help="Check ephys data or not."),
    ] = True,
    check_videos: Annotated[
        bool,
        typer.Option("--check-videos/--ignore-videos", help="Check videos data or not."),
    ] = True,
):
    """
    Validate experimental data in a given session.

    E.g. to check all kinds of data in the current working directory which is supposedly a session of subject called M017:

        `bnd validate-session . M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not check_behavior, not check_ephys, not check_videos]):
        raise ValueError("At least one data type must be checked.")

    if not session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not session_path.absolute().exists():
        raise ValueError("Session path does not exist.")

    validate_raw_session(
        session_path.absolute(),
        subject_name,
        check_behavior,
        check_ephys,
        check_videos,
    )


def validate_last(
    subject_name: Annotated[
        str,
        typer.Argument(
            help="Name of the subject the session belongs to. (Used for confirmation.)"
        ),
    ],
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session. raw or processed.")
    ] = "raw",
    check_locally: Annotated[
        bool,
        typer.Option("--local/--remote", help="Check local or remote data."),
    ] = True,
    check_behavior: Annotated[
        bool,
        typer.Option(
            "--check-behavior/--ignore-behavior", help="Check behavioral data or not."
        ),
    ] = True,
    check_ephys: Annotated[
        bool,
        typer.Option("--check-ephys/--ignore-ephys", help="Check ephys data or not."),
    ] = True,
    check_videos: Annotated[
        bool,
        typer.Option("--check-videos/--ignore-videos", help="Check videos data or not."),
    ] = True,
):
    """
    Validate experimental data in the last session of a subject.

    Example usage:
        `bnd validate-last M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not check_behavior, not check_ephys, not check_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()

    root_path = config.LOCAL_PATH if check_locally else config.REMOTE_PATH

    subject_path = root_path / processing_level / subject_name

    # get the last valid session
    last_session_path = get_last_session_path(subject_path, subject_name).absolute()

    print(f"[bold]Last session found: [green]{last_session_path.name}", end="\n\n")

    validate_raw_session(
        last_session_path,
        subject_name,
        check_behavior,
        check_ephys,
        check_videos,
    )
