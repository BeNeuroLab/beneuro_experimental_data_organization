from pathlib import Path
from typing_extensions import Annotated
import datetime

import typer
from rich import print

from beneuro_data.query_sessions import (
    get_last_session_path,
    list_subject_sessions_on_day,
    list_all_sessions_on_day,
)
from beneuro_data.data_validation import validate_raw_session
from beneuro_data.data_transfer import upload_raw_session, download_raw_session
from beneuro_data.video_renaming import rename_raw_videos_of_session
from beneuro_data.config import _get_env_path, _load_config
from beneuro_data.update_bnd import update_bnd


app = typer.Typer()


@app.command()
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


@app.command()
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


@app.command()
def rename_videos(
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
    verbose: Annotated[
        bool,
        typer.Option(help="Print the list of files that were renamed."),
    ] = False,
):
    """
    Rename the raw videos saved by Jarvis during a session to the convention we use.

    Example usage:

        `bnd rename-videos . M017 --verbose`

        `bnd rename-videos /absolute/path/to/session M017 --verbose`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if not session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not session_path.absolute().exists():
        raise ValueError("Session path does not exist.")

    rename_raw_videos_of_session(
        session_path.absolute(),
        subject_name,
        verbose,
    )


@app.command()
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


@app.command()
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


@app.command()
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


@app.command()
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


@app.command()
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


@app.command()
def show_config():
    """
    Show the contents of the config file.
    """
    config = _load_config()
    print(config.json(indent=4))


def _check_root(root_path: Path):
    assert root_path.exists(), f"{root_path} does not exist."
    assert root_path.is_dir(), f"{root_path} is not a directory."

    files_in_root = [f.stem for f in root_path.iterdir()]

    assert "raw" in files_in_root, f"No raw folder in {root_path}"
    assert "processed" in files_in_root, f"No processed folder in {root_path}"


@app.command()
def check_config():
    """
    Check that the local and remote root folders have the expected raw and processed folders.
    """
    config = _load_config()

    print(
        "Checking that local and remote root folders have the expected raw and processed folders..."
    )

    _check_root(config.LOCAL_PATH)
    _check_root(config.REMOTE_PATH)

    print("[green]Config looks good.")


@app.command()
def init():
    """
    Create a .env file to store the paths to the local and remote data storage.
    """

    # check if the file exists
    env_path = _get_env_path()

    if env_path.exists():
        print("\n[yellow]Config file already exists.\n")

        check_config()

    else:
        print("\nConfig file doesn't exist. Let's create one.")

        local_path = Path(
            typer.prompt("Enter the absolute path to the root of the local data storage")
        )
        _check_root(local_path)
        remote_path = Path(
            typer.prompt("Enter the absolute path to the root of remote data storage")
        )
        _check_root(remote_path)

        with open(env_path, "w") as f:
            f.write(f"LOCAL_PATH = {local_path}\n")
            f.write(f"REMOTE_PATH = {remote_path}\n")

        # make sure that it works
        config = _load_config()
        _check_root(config.LOCAL_PATH)
        _check_root(config.REMOTE_PATH)

        print("[green]Config file created successfully.")


@app.command()
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


@app.command()
def download_session(
    remote_session_path: Annotated[
        Path,
        typer.Argument(
            help="Path to session directory on the server. Can be relative or absolute"
        ),
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
    Download (raw) experimental data in a given session from the remote server.

    Example usage:
        `bnd download-session . M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not include_behavior, not include_ephys, not include_videos]):
        raise ValueError("At least one data type must be checked.")

    config = _load_config()

    download_raw_session(
        remote_session_path.absolute(),
        subject_name,
        config.LOCAL_PATH,
        config.REMOTE_PATH,
        include_behavior,
        include_ephys,
        include_videos,
    )

    return True


@app.command()
def download_last(
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
            "--include-behavior/--ignore-behavior", help="Download behavioral data or not."
        ),
    ] = True,
    include_ephys: Annotated[
        bool,
        typer.Option("--include-ephys/--ignore-ephys", help="Download ephys data or not."),
    ] = True,
    include_videos: Annotated[
        bool,
        typer.Option(
            "--include-videos/--ignore-videos", help="Download videos data or not."
        ),
    ] = True,
):
    """
    Download (raw) experimental data in the last session of a subject from the remote server.

    Example usage:
        `bnd download-last M017`
    """
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all([not include_behavior, not include_ephys, not include_videos]):
        raise ValueError("At least one data type must be downloaded.")

    config = _load_config()

    subject_path = config.REMOTE_PATH / processing_level / subject_name

    # get the last valid session
    last_session_path = get_last_session_path(subject_path, subject_name).absolute()

    # TODO Error messages don't make sense because downloading uses the upload function
    # TODO Should remote files be checked the same way before downloading
    # the same way local files are checked before uploading?
    download_raw_session(
        last_session_path.absolute(),
        subject_name,
        config.LOCAL_PATH,
        config.REMOTE_PATH,
        include_behavior,
        include_ephys,
        include_videos,
    )

    return True


if __name__ == "__main__":
    app()
