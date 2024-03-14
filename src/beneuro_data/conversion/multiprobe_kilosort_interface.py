from pathlib import Path
from typing import Optional

from neuroconv.datainterfaces import KiloSortSortingInterface
from neuroconv.utils import DeepDict, FolderPathType
from pynwb import NWBFile


class MultiProbeKiloSortInterface(KiloSortSortingInterface):
    def __init__(
        self,
        # folder_paths: tuple[FolderPathType, ...],
        processed_recording_path: FolderPathType,
        keep_good_only: bool = False,
        verbose: bool = True,
    ):
        kilosort_folder_paths = list(
            Path(processed_recording_path).glob("**/sorter_output")
        )
        self.probe_names = [
            ks_path.parent.name.split("_")[-1] for ks_path in kilosort_folder_paths
        ]

        self.kilosort_interfaces = [
            KiloSortSortingInterface(folder_path, keep_good_only, verbose)
            for folder_path in kilosort_folder_paths
        ]

        self.processed_recording_path = Path(processed_recording_path)

    def set_aligned_starting_time(self, aligned_starting_time: float):
        for kilosort_interface in self.kilosort_interfaces:
            kilosort_interface.set_aligned_starting_time(aligned_starting_time)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[DeepDict] = None,
        stub_test: bool = False,
        # write_ecephys_metadata: bool = True,
        # write_as: Literal["units", "processing"] = "units",
        # units_name: str = "units",
        # units_description: str = "Autogenerated by neuroconv.",
    ):
        # Kilosort output will be saved in processing and not units
        # units is reserved for the units curated by Phy
        for probe_name, kilosort_interface in zip(
            self.probe_names, self.kilosort_interfaces
        ):
            kilosort_interface.add_to_nwbfile(
                nwbfile,
                metadata,
                stub_test,
                write_ecephys_metadata=True,
                write_as="processing",  # kilosort output is not the final curated version
                units_name=f"units_{probe_name}",
                units_description=f"Kilosorted units on {probe_name}",
            )

            # The following does add the probes to the NWB file but without any useful info,
            # so I'll use probeinterface for that
            # raw_recording_path = Path(str(self.processed_recording_path).replace("processed", "raw"))
            # recording = se.read_spikeglx(
            #    raw_recording_path,
            #    stream_name = f"{probe_name}.ap",
            #    load_sync_channel = True,
            # )

            # from neuroconv.tools.spikeinterface import (
            #    add_devices,
            #    add_electrode_groups,
            #    add_electrodes,
            # )

            # add_devices(nwbfile=nwbfile, metadata=metadata)
            # add_electrode_groups(recording=recording, nwbfile=nwbfile, metadata=metadata)
            # add_electrodes(recording=recording, nwbfile=nwbfile, metadata=metadata)

    def get_metadata(self) -> DeepDict:
        return DeepDict()
