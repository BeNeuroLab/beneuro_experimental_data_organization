import warnings
from pathlib import Path

from typing import Optional

from beneuro_data.spike_sorting import run_kilosort_on_session_and_save_in_processed

from beneuro_data.conversion.beneuro_converter import BeNeuroConverter

from beneuro_data.data_validation import (
    validate_raw_session,
    _find_spikeglx_recording_folders_in_session,
)


def convert_to_nwb(
    raw_session_path: Path,
    subject_name: str,
    base_path: Path,
    whitelisted_files_in_root: tuple[str, ...],
    allowed_extensions_not_in_root: tuple[str, ...],
    run_kilosort: bool,
    stream_names_to_process: Optional[tuple[str, ...]] = None,
    clean_up_temp_files: Optional[bool] = False,
):
    # make sure the kilosort arguments are given
    if run_kilosort:
        assert allowed_extensions_not_in_root is not None
        assert stream_names_to_process is not None
        assert clean_up_temp_files is not None

    # validate session before doing any conversion
    validate_raw_session(
        raw_session_path,
        subject_name,
        include_behavior=True,
        include_ephys=True,
        include_videos=True,
        whitelisted_files_in_root=whitelisted_files_in_root,
        allowed_extensions_not_in_root=whitelisted_files_in_root,
    )

    # make sure the paths are Path objects and consistent with each other
    if isinstance(raw_session_path, str):
        raw_session_path = Path(raw_session_path)
    if isinstance(base_path, str):
        base_path = Path(base_path)
    if not raw_session_path.is_relative_to(base_path / "raw"):
        raise ValueError(f"{raw_session_path} is not in {base_path / 'raw'}")

    raw_recording_path = _find_spikeglx_recording_folders_in_session(raw_session_path)[0]

    recording_folder_name = raw_recording_path.name
    session_folder_name = raw_session_path.name

    # determine output path
    raw_base_path = base_path / "raw"
    processed_base_path = base_path / "processed"
    processed_session_path = processed_base_path / raw_session_path.relative_to(
        raw_base_path
    )
    processed_recording_ephys_path = (
        processed_session_path / f"{session_folder_name}_ephys" / recording_folder_name
    )

    nwb_file_output_path = processed_session_path / f"{session_folder_name}.nwb"
    if nwb_file_output_path.exists():
        raise FileExistsError(f"NWB file already exists at {nwb_file_output_path}")

    raw_probe_folders = sorted([p.name for p in raw_recording_path.iterdir() if p.is_dir()])
    processed_probe_folders = sorted(
        [p.name for p in processed_recording_ephys_path.iterdir() if p.is_dir()]
    )
    if (not run_kilosort) and (raw_probe_folders != processed_probe_folders):
        warnings.warn(
            "Looks like not all probes have been kilosorted. You might want to do it."
        )

    if run_kilosort:
        run_kilosort_on_session_and_save_in_processed(
            raw_session_path,
            subject_name,
            base_path,
            allowed_extensions_not_in_root,
            stream_names_to_process,
            clean_up_temp_files,
        )

    source_data = dict(
        PyControl={"file_path": str(raw_session_path)},
        KiloSort={
            "processed_recording_path": str(processed_session_path),
        },
    )

    converter = BeNeuroConverter(source_data)

    converter.run_conversion(
        metadata=converter.get_metadata(),
        nwbfile_path=nwb_file_output_path,
    )

    return nwb_file_output_path