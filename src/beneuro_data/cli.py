from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from typing_extensions import Annotated

from beneuro_data.config import (
    _check_is_git_track,
    _check_root,
    _get_env_path,
    _get_package_path,
    _load_config,
)
from beneuro_data.data_transfer import download_raw_session, upload_raw_session
from beneuro_data.query_sessions import (
    get_last_session_path,
)
from beneuro_data.update_bnd import check_for_updates, update_bnd

app = typer.Typer()


@app.command()
def to_pyal(
    session_name: Annotated[
        str,
        typer.Argument(help="Session name to convert"),
    ],
    run_kilosort: Annotated[
        bool,
        typer.Option("-k/-K", help="Run Kilosort 4 or not"),
    ] = False,
    run_anipose: Annotated[
        bool,
        typer.Option("-a/-A", help="Run Anipose or not"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("-v/-V", help="Verbosity on pyaldata conversion"),
    ] = True,
):
    """
    Convert session data into a pyaldata dataframe and saves it as a .mat

    You can optionally include ephys and pose estimation but behaviour is a must.


    \b
    Basic usage:
        `bnd to-pyal M037_2024_01_01_10_00`

    \b
    Verbosity:
        `bnd to-pyal M037_2024_01_01_10_00 --verbose`


    """
    # TODO: Make custom channel map option in case we dont agree with pinpoint

    from beneuro_data.conversion.convert_nwb_to_pyaldata import convert_nwb_to_pyaldata

    config = _load_config()
    local_session_path = config.get_local_session_path(session_name, "raw")

    if not local_session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not local_session_path.absolute().exists():
        raise ValueError("Session path does not exist.")
    if not local_session_path.absolute().is_relative_to(config.LOCAL_PATH):
        raise ValueError("Session path must be inside the local root folder.")

    # Check if there already a pyaldaya file
    if (local_session_path / f"{session_name}_pyaldata.mat").exists():
        while True:
            user_input = (
                input(
                    f"File '{(local_session_path / f"{session_name}_pyaldata.mat").name}' already exists. Do you want to overwrite it? (y/n): "
                )
                .lower()
                .strip()
            )
            if user_input == "n":
                print(
                    f"File '{(local_session_path / f"{session_name}_pyaldata.mat").name}' was not overwritten."
                )
                return
            elif user_input == "y":
                nwbfiles = list(local_session_path.glob("*.nwb"))
                if len(nwbfiles) > 1:
                    raise FileNotFoundError("Too many nwb files in session folder!")
                elif not nwbfiles:
                    if verbose:
                        print("No nwb file found, creating one")
                    to_nwb(
                        session_name=session_name,
                        run_kilosort=run_kilosort,
                        run_anipose=run_anipose,
                        verbose=verbose,
                    )

    nwbfile_path = list(local_session_path.glob("*.nwb"))[0].absolute()

    # Run conversion
    convert_nwb_to_pyaldata(nwbfile_path, verbose)


@app.command()
def to_nwb(
    session_name: Annotated[
        str,
        typer.Argument(help="Session name to convert"),
    ],
    run_kilosort: Annotated[
        bool,
        typer.Option("-k/-K", help="Run Kilosort 4 or not"),
    ] = False,
    run_anipose: Annotated[
        bool,
        typer.Option("-a/-A", help="Run Anipose or not"),
    ] = False,
    clean_up_temp_files: Annotated[
        bool,
        typer.Option(
            "--clean-up-temp-files/--keep-temp-files",
            help="Keep the binary files created by Kilosort or not. They are huge, but needed for running Phy later.",
        ),
    ] = True,
    sort_probe: Annotated[
        Optional[List[str]],
        typer.Option(
            help="Probes to run Kilosort on. If not given, all probes are processed."
        ),
    ] = None,
    verbose_kilosort: Annotated[
        bool,
        typer.Option(help="Run Kilosort in verbose mode."),
    ] = True,
):
    """
    Convert a session's data to NWB, optionally running Kilosort before.

    Includes:

        - behavioral events and ball position from PyControl

        - session and subject details from the .profile file

        - spikes from Kilosort

        - pose estimation from sleap-anipose



    Note that you will need some extra dependencies that are not installed by default.

    You can install them by running `poetry install --with processing` in bnd's root folder (which you can with with `bnd show-config`).



    \b
    Basic usage:
        `bnd to-nwb M037_2024_01_01_10_00`

    \b
    Run Kilosort:
        `bnd to-nwb M037_2024_01_01_10_00 --kilosort`

    \b
    Running Kilosort on only selected probes:
        `bnd to-nwb M037_2024_01_01_10_00 --sort-probe imec0 --sort-probe imec1`
    """
    # this will throw an error if the dependencies are not available
    from beneuro_data.conversion.convert_to_nwb import convert_to_nwb

    config = _load_config()
    local_session_path = config.get_local_session_path(session_name, "raw")
    subject_name = config.get_animal_name(session_name)

    if not local_session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not local_session_path.absolute().exists():
        raise ValueError("Session path does not exist.")
    if not local_session_path.absolute().is_relative_to(config.LOCAL_PATH):
        raise ValueError("Session path must be inside the local root folder.")

    if len(sort_probe) != 0:
        if len(set(sort_probe)) != len(sort_probe):
            raise ValueError(f"Duplicate probe names found in {sort_probe}.")
        # append .ap to each probe name
        stream_names_to_process = [f"{probe}.ap" for probe in sort_probe]
        # check that they are all in the session folder somewhere
        for stream_name in stream_names_to_process:
            if len(list(local_session_path.glob(f"**/*{stream_name}.bin"))) == 0:
                raise ValueError(
                    f"No file found for {stream_name} in {local_session_path.absolute()}"
                )
    else:
        stream_names_to_process = None

    convert_to_nwb(
        local_session_path.absolute(),
        subject_name,
        config.LOCAL_PATH,
        config.WHITELISTED_FILES_IN_ROOT,
        config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        run_kilosort,
        stream_names_to_process,
        clean_up_temp_files,
        verbose_kilosort,
    )


@app.command()
def dl(
    session_name: Annotated[
        str, typer.Argument(help="Name of session: M123_2000_02_03_14_15")
    ],
    include_behavior: Annotated[
        bool,
        typer.Option(
            "--include-behavior/--ignore-behavior",
            "-b/-B",
            help="Download behavioral data (-b) or not (-B).",
        ),
    ] = True,
    include_ephys: Annotated[
        bool,
        typer.Option(
            "--include-ephys/--ignore-ephys",
            "-e/-E",
            help="Download ephys data (-e) or not (-E).",
        ),
    ] = False,
    include_videos: Annotated[
        bool,
        typer.Option(
            "--include-videos/--ignore-videos",
            "-v/-V",
            help="Download video data (-v) or not (-V).",
        ),
    ] = False,
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session must be raw.")
    ] = "raw",
    include_kilosort: Annotated[
        bool,
        typer.Option(
            "--include-kilosort-output/--ignore-kilosort-output",
            "-k/-K",
            help="Upload Kilosort output (-k) or not (-K).",
        ),
    ] = False,
    include_nwb: Annotated[
        bool,
        typer.Option(
            "--include-nwb/--ignore-nwb",
            "-n/-N",
            help="Download NWB files (-n) or not (-N).",
        ),
    ] = False,
    include_pyaldata: Annotated[
        bool,
        typer.Option(
            "--include-pyaldata/--ignore-pyaldata",
            "-p/-P",
            help="Download PyalData files (-p) or not (-P).",
        ),
    ] = False,
):
    """
    Download (raw) experimental data from a given session from the remote server.

    Example usage to download everything:
        `bnd dl M017_2024_03_12_18_45 -ev`
    """
    animal = session_name[:4]
    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all(
        [
            not include_behavior,
            not include_ephys,
            not include_videos,
            not include_kilosort,
            not include_nwb,
            not include_pyaldata,
        ]
    ):
        raise ValueError("At least one data type must be included.")

    config = _load_config()

    download_raw_session(
        remote_session_path=config.REMOTE_PATH / processing_level / animal / session_name,
        subject_name=animal,
        local_base_path=config.LOCAL_PATH,
        remote_base_path=config.REMOTE_PATH,
        include_behavior=include_behavior,
        include_ephys=include_ephys,
        include_videos=include_videos,
        whitelisted_files_in_root=config.WHITELISTED_FILES_IN_ROOT,
        allowed_extensions_not_in_root=config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        include_nwb=include_nwb,
        include_pyaldata=include_pyaldata,
        include_kilosort=include_kilosort,
    )
    print(f"Session {session_name} downloaded.")

    return True


@app.command()
def ksort(
    session_name: Annotated[
        str,
        typer.Argument(help="Session name to convert"),
    ],
    probes: Annotated[
        Optional[List[str]],
        typer.Argument(
            help="List of probes to process. If nothing is given, all probes are processed."
        ),
    ] = None,
    clean_up_temp_files: Annotated[
        bool,
        typer.Option(
            "--clean-up-temp-files/--keep-temp-files",
            help="Keep the binary files created or not. They are huge, but needed for running Phy later.",
        ),
    ] = True,
    verbose: Annotated[
        bool, typer.Option(help="Print info about what is being run.")
    ] = True,
):
    """
    Run Kilosort 4 on a session and save the results in the raw folder.

    Note that you will need some extra dependencies that are not installed by default. You can install them by running `poetry install --with processing` in bnd's root folder.

    \b
    Basic usage:
        `bnd kilosort-session M020_2024_01_01_10_00`

    \b
    Only sorting specific probes:
        `bnd kilosort-session M020_2024_01_01_10_00 imec0`
        `bnd kilosort-session M020_2024_01_01_10_00 imec0 imec1`

    \b
    Keeping binary files useful for Phy:
        `bnd kilosort-session M020_2024_01_01_10_00 --keep-temp-files`

    \b
    Suppressing output:
        `bnd kilosort-session M020_2024_01_01_10_00 --no-verbose`
    """
    # this will throw an error if the dependencies are not available
    from beneuro_data.spike_sorting import run_kilosort_on_session_and_save_in_raw

    config = _load_config()
    local_session_path = config.get_local_session_path(session_name, "raw")
    subject_name = config.get_animal_name(session_name)

    if not local_session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not local_session_path.absolute().exists():
        raise ValueError("Session path does not exist.")
    if not local_session_path.absolute().is_relative_to(config.LOCAL_PATH):
        raise ValueError("Session path must be inside the local root folder.")

    if len(probes) != 0:
        if len(set(probes)) != len(probes):
            raise ValueError(f"Duplicate probe names found in {probes}.")
        # append .ap to each probe name
        stream_names_to_process = [f"{probe}.ap" for probe in probes]
        # check that they are all in the session folder somewhere
        for stream_name in stream_names_to_process:
            if len(list(local_session_path.glob(f"**/*{stream_name}.bin"))) == 0:
                raise ValueError(
                    f"No file found for {stream_name} in {local_session_path.absolute()}"
                )
    else:
        stream_names_to_process = None

    run_kilosort_on_session_and_save_in_raw(
        local_session_path.absolute(),
        subject_name,
        config.LOCAL_PATH,
        config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        stream_names_to_process=stream_names_to_process,
        clean_up_temp_files=clean_up_temp_files,
        verbose=verbose,
    )


@app.command()
def up(
    session_or_animal_name: Annotated[
        str, typer.Argument(help="Animal or session name: M123 or M123_2000_02_03_14_15")
    ],
    include_behavior: Annotated[
        bool,
        typer.Option(
            "--include-behavior/--ignore-behavior",
            "-b/-B",
            help="Upload behavioral data (-b) or not (-B).",
        ),
    ] = False,
    include_ephys: Annotated[
        bool,
        typer.Option(
            "--include-ephys/--ignore-ephys",
            "-e/-E",
            help="Upload ephys data (-e) or not (-E).",
        ),
    ] = False,
    include_videos: Annotated[
        bool,
        typer.Option(
            "--include-videos/--ignore-videos",
            "-v/-V",
            help="Upload video data (-v) or not (-V).",
        ),
    ] = False,
    include_nwb: Annotated[
        bool,
        typer.Option(
            "--include-nwb/--ignore-nwb",
            "-n/-N",
            help="Upload NWB files (-n) or not (-N).",
        ),
    ] = False,
    include_pyaldata: Annotated[
        bool,
        typer.Option(
            "--include-pyaldata/--ignore-pyaldata",
            "-p/-P",
            help="Upload PyalData files (-p) or not (-P).",
        ),
    ] = False,
    include_kilosort: Annotated[
        bool,
        typer.Option(
            "--include-kilosort-output/--ignore-kilosort-output",
            "-k/-K",
            help="Upload Kilosort output (-k) or not (-K).",
        ),
    ] = False,
    include_extra_files: Annotated[
        bool,
        typer.Option(
            "--include-extra-files/--ignore-extra-files",
            help="Upload extra files that are created by the experimenter or other software.",
        ),
    ] = True,
    rename_videos_first: Annotated[
        bool,
        typer.Option(
            "--rename/--no-rename",
            help="Rename videos before validating and uploading.",
        ),
    ] = None,
    rename_extra_files_first: Annotated[
        bool,
        typer.Option(
            "--rename-extra/--no-rename-extra",
            help="Rename extra files (e.g. comment.txt) before validating and uploading.",
        ),
    ] = True,
):
    """
    Upload (raw) experimental data to the remote server.

    Example usage to upload everything of a given session:
        `bnd up M017_2024_03_12_18_45 -ev`
    Example to upload the videos and ephys of the last session of a subject:
        `bnd up M017 -evB`
    """
    config = _load_config()
    animal = config.get_animal_name(session_or_animal_name)

    if all(
        [
            not include_behavior,
            not include_ephys,
            not include_videos,
            not include_nwb,
            not include_pyaldata,
            not include_kilosort,
        ]
    ):
        raise ValueError("At least one data type must be included.")

    # if videos are included, rename them first if not specified otherwise
    if rename_videos_first is None:
        rename_videos_first = include_videos

    if rename_videos_first and not include_videos:
        raise ValueError(
            "Do not rename videos if you're not uploading them. (Meaning --ignore-videos and --rename-videos are not allowed together.)"
        )

    config = _load_config()

    if len(session_or_animal_name) > 4:  # session name is given
        up_done = upload_raw_session(
            config.LOCAL_PATH / "raw" / animal / session_or_animal_name,
            animal,
            config.LOCAL_PATH,
            config.REMOTE_PATH,
            include_behavior,
            include_ephys,
            include_videos,
            include_extra_files,
            config.WHITELISTED_FILES_IN_ROOT,
            config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
            rename_videos_first,
            rename_extra_files_first,
            include_nwb=include_nwb,
            include_pyaldata=include_pyaldata,
            include_kilosort=include_kilosort,
        )
        message = f"Session {session_or_animal_name} uploaded."
    else:  # only animal name is given
        up_done = upload_last(
            animal,
            include_behavior,
            include_ephys,
            include_videos,
            include_extra_files,
            rename_videos_first,
            rename_extra_files_first,
            include_nwb=include_nwb,
            include_pyaldata=include_pyaldata,
            include_kilosort=include_kilosort,
        )
        message = f"Last session of {animal} uploaded."
    if up_done:
        print(message)

    return True


@app.command()
def upload_last(
    subject_name: Annotated[
        str,
        typer.Argument(help="Name of the subject the session belongs to."),
    ],
    include_behavior: Annotated[
        bool,
        typer.Option(
            "--include-behavior/--ignore-behavior",
            help="Upload behavioral data or not.",
        ),
    ] = None,
    include_ephys: Annotated[
        bool,
        typer.Option(
            "--include-ephys/--ignore-ephys",
            help="Upload ephys data or not.",
        ),
    ] = None,
    include_videos: Annotated[
        bool,
        typer.Option(
            "--include-videos/--ignore-videos",
            help="Upload video data or not.",
        ),
    ] = None,
    include_extra_files: Annotated[
        bool,
        typer.Option(
            "--include-extra-files/--ignore-extra-files",
            help="Upload extra files that are created by the experimenter or other software.",
        ),
    ] = True,
    rename_videos_first: Annotated[
        bool,
        typer.Option(
            "--rename-videos/--no-rename-videos",
            help="Rename videos before validating and uploading. Defaults to True if including videos, to False if not.",
        ),
    ] = None,
    rename_extra_files_first: Annotated[
        bool,
        typer.Option(
            "--rename-extra-files/--no-rename-extra-files",
            help="Rename extra files (e.g. comment.txt) before validating and uploading.",
        ),
    ] = True,
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session must be raw.")
    ] = "raw",
    include_nwb: Annotated[
        bool,
        typer.Option(
            "--include-nwb/--ignore-nwb",
            help="Upload NWB files or not.",
        ),
    ] = None,
    include_pyaldata: Annotated[
        bool,
        typer.Option(
            "--include-pyaldata/--ignore-pyaldata",
            help="Upload PyalData files or not.",
        ),
    ] = None,
    include_kilosort: Annotated[
        bool,
        typer.Option(
            "--include-kilosort-output/--ignore-kilosort-output",
            "-k/-K",
            help="Upload Kilosort output (-k) or not (-K).",
        ),
    ] = None,
):
    """
    Upload (raw) experimental data in the last session of a subject to the remote server.

    Example usage:
        `bnd upload-last M017`
    """

    config = _load_config()

    subject_path = config.LOCAL_PATH / "raw" / subject_name

    # first get the last valid session
    # and ask the user if this is really the session they want to upload
    last_session_path = get_last_session_path(subject_path, subject_name).absolute()

    typer.confirm(
        f"{last_session_path.name} is the last session for {subject_name}. Upload?",
        abort=True,
    )

    # then ask the user if they want to include behavior, ephys, and videos
    # only ask the ones that are not specified as a CLI option
    if include_behavior is None:
        include_behavior = typer.confirm("Include behavior?")
    if include_ephys is None:
        include_ephys = typer.confirm("Include ephys?")
    if include_videos is None:
        include_videos = typer.confirm("Include videos?")
    if include_kilosort is None:
        include_kilosort = typer.confirm("Include Kilosort output?")
    if include_nwb is None:
        include_nwb = typer.confirm("Include NWB files?")
    if include_pyaldata is None:
        include_pyaldata = typer.confirm("Include PyalData files?")

    if all(
        [
            not include_behavior,
            not include_ephys,
            not include_videos,
            not include_kilosort,
            not include_nwb,
            not include_pyaldata,
        ]
    ):
        raise ValueError("At least one data type must be included.")

    # if videos are included, rename them first if not specified otherwise
    if rename_videos_first is None:
        rename_videos_first = include_videos

    if rename_videos_first and not include_videos:
        raise ValueError(
            "Do not rename videos if you're not uploading them. (Meaning --ignore-videos and --rename-videos are not allowed together.)"
        )

    upload_raw_session(
        last_session_path,
        subject_name,
        config.LOCAL_PATH,
        config.REMOTE_PATH,
        include_behavior,
        include_ephys,
        include_videos,
        include_extra_files,
        config.WHITELISTED_FILES_IN_ROOT,
        config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        rename_videos_first,
        rename_extra_files_first,
        include_nwb=include_nwb,
        include_pyaldata=include_pyaldata,
        include_kilosort=include_kilosort,
    )

    return True


@app.command()
def show_config():
    """
    Show the contents of the config file.
    """
    config = _load_config()
    print(f"bnd source code is at {_get_package_path()}", end="\n\n")
    print(config.json(indent=4))


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
        repo_path = Path(typer.prompt("Enter the absolute path to the repository"))
        _check_is_git_track(repo_path)

        local_path = Path(
            typer.prompt("Enter the absolute path to the root of the local data storage")
        )
        _check_root(local_path)

        remote_path = Path(
            typer.prompt("Enter the absolute path to the root of remote data storage")
        )
        _check_root(remote_path)

        with open(env_path, "w") as f:
            f.write(f"REPO_PATH = {repo_path}\n")
            f.write(f"LOCAL_PATH = {local_path}\n")
            f.write(f"REMOTE_PATH = {remote_path}\n")

        # make sure that it works
        config = _load_config()
        _check_root(config.LOCAL_PATH)
        _check_root(config.REMOTE_PATH)

        print("[green]Config file created successfully.")


@app.command()
def check_updates():
    """
    Check if there are any new commits on the repo's main branch.
    """
    check_for_updates()


@app.command()
def self_update(
    install_method: Annotated[
        str,
        typer.Option(
            "-m",
            "--method",
            help="Specify the installation method: 'conda' or 'poetry'.",
            case_sensitive=False,
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(help="Print new commits that were pulled."),
    ] = True,
):
    """
    Update the bnd tool by pulling the latest commits from the repo's main branch.
    """
    update_bnd(install_method=install_method, print_new_commits=verbose)


"""

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
        str, typer.Argument(help="Processing level of the session must be raw.")
    ] = "raw",
    verbose: Annotated[
        bool,
        typer.Option(help="Print the list of files that were renamed."),
    ] = False,
):
    Rename the raw videos saved by Jarvis during a session to the convention we use.

    Example usage:

        `bnd rename-videos . M017 --verbose`

        `bnd rename-videos /absolute/path/to/session M017 --verbose`
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
"""

"""
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
        str, typer.Argument(help="Processing level of the session must be raw.")
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
    check_nwb: Annotated[
        bool,
        typer.Option(
            "--check-nwb/--ignore-nwb",
            help="Check NWB files or not.",
        ),
    ] = False,
    check_pyaldata: Annotated[
        bool,
        typer.Option(
            "--check-pyaldata/--ignore-pyaldata",
            help="Check PyalData files or not.",
        ),
    ] = False,
    check_kilosort: Annotated[
        bool,
        typer.Option(
            "--check-kilosort-output/--ignore-kilosort-output",
            help="Check Kilosort output or not.",
        ),
    ] = False,
):
    Validate experimental data in a given session.

    E.g. to check all kinds of data in the current working directory which is supposedly a session of subject called M017:

        `bnd validate-session . M017`

    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all(
        [
            not check_behavior,
            not check_ephys,
            not check_videos,
            not check_kilosort,
            not check_nwb,
            not check_pyaldata,
        ]
    ):
        raise ValueError("At least one data type must be checked.")

    if not session_path.absolute().is_dir():
        raise ValueError("Session path must be a directory.")
    if not session_path.absolute().exists():
        raise ValueError("Session path does not exist.")

    config = _load_config()

    validate_raw_session(
        session_path.absolute(),
        subject_name,
        check_behavior,
        check_ephys,
        check_videos,
        config.WHITELISTED_FILES_IN_ROOT,
        config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        check_nwb=check_nwb,
        check_pyaldata=check_pyaldata,
        check_kilosort=check_kilosort,
    )
    """

"""
@app.command()
def validate_last(
    subject_name: Annotated[
        str,
        typer.Argument(
            help="Name of the subject the session belongs to. (Used for confirmation.)"
        ),
    ],
    processing_level: Annotated[
        str, typer.Argument(help="Processing level of the session must be raw.")
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
    check_nwb: Annotated[
        bool,
        typer.Option(
            "--check-nwb/--ignore-nwb",
            help="Check NWB files or not.",
        ),
    ] = False,
    check_pyaldata: Annotated[
        bool,
        typer.Option(
            "--check-pyaldata/--ignore-pyaldata",
            help="Check PyalData files or not.",
        ),
    ] = False,
    check_kilosort: Annotated[
        bool,
        typer.Option(
            "--check-kilosort-output/--ignore-kilosort-output",
            help="Check Kilosort output or not.",
        ),
    ] = False,
):
    Validate experimental data in the last session of a subject.

    Example usage:
        `bnd validate-last M017`

    if processing_level != "raw":
        raise NotImplementedError("Sorry, only raw data is supported for now.")

    if all(
        [
            not check_behavior,
            not check_ephys,
            not check_videos,
            not check_kilosort,
            not check_nwb,
            not check_pyaldata,
        ]
    ):
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
        config.WHITELISTED_FILES_IN_ROOT,
        config.EXTENSIONS_TO_RENAME_AND_UPLOAD,
        check_nwb=check_nwb,
        check_pyaldata=check_pyaldata,
        check_kilosort=check_kilosort,
    )
    """


if __name__ == "__main__":
    app()
