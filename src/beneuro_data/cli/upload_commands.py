from pathlib import Path
from typing_extensions import Annotated

import typer

from beneuro_data.query_sessions import get_last_session_path

from beneuro_data.data_transfer import upload_raw_session
from beneuro_data.config import _load_config


def upload_last(
    subject_name: Annotated[
        str,
        typer.Argument(help="Name of the subject the session belongs to."),
    ],
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session. raw or processed.")
    ] = "raw",
    include_behavior: Annotated[
        bool,
        typer.Option(
            "--include-behavior/--ignore-behavior", help="Upload behavioral data or not."
        ),
    ] = True,
    include_ephys: Annotated[
        bool,
        typer.Option("--include-ephys/--ignore-ephys", help="Upload ephys data or not."),
    ] = True,
    include_videos: Annotated[
        bool,
        typer.Option("--include-videos/--ignore-videos", help="Upload videos data or not."),
    ] = True,
):
    """
    Upload (raw) experimental data in the last session of a subject to the remote server.

    Example usage:
        `bnd upload-last M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not include_behavior, not include_ephys, not include_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()

    subject_path = config.LOCAL_PATH / processing_level / subject_name

    # get the last valid session
    last_session_path = get_last_session_path(subject_path, subject_name).absolute()

    # ask the user if this is really the session they want to upload
    typer.confirm(
        f"{last_session_path.name} is the last session for {subject_name}. Upload?",
        abort=True,
    )

    upload_raw_session(
        last_session_path,
        subject_name,
        config.LOCAL_PATH,
        config.REMOTE_PATH,
        include_behavior,
        include_ephys,
        include_videos,
    )

    return True


def upload_session(
    local_session_path: Annotated[
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
    include_behavior: Annotated[
        bool,
        typer.Option(
            "--include-behavior/--ignore-behavior", help="Upload behavioral data or not."
        ),
    ] = True,
    include_ephys: Annotated[
        bool,
        typer.Option("--include-ephys/--ignore-ephys", help="Upload ephys data or not."),
    ] = True,
    include_videos: Annotated[
        bool,
        typer.Option("--include-videos/--ignore-videos", help="Upload videos data or not."),
    ] = True,
):
    """
    Upload (raw) experimental data in a given session to the remote server.

    Example usage:
        `bnd upload-session . M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not include_behavior, not include_ephys, not include_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()

    upload_raw_session(
        local_session_path.absolute(),
        subject_name,
        config.LOCAL_PATH,
        config.REMOTE_PATH,
        include_behavior,
        include_ephys,
        include_videos,
    )

    return True
