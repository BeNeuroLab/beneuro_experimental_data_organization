import pytest

import os
import shutil
import pathlib
from dataclasses import dataclass
from typing import Type, Optional

from ruamel.yaml import YAML

from beneuro_data.data_validation import Subject

from generate_directory_structure_test_cases import create_directory_structure_from_dict


TEST_DIR_PATH = os.path.dirname(__file__)
YAML_FOLDER = os.path.join(TEST_DIR_PATH, "directory_structure_test_yamls")


@dataclass
class DirectoryStructureTestCase:
    yaml_name: str
    error_type: Optional[Type]
    error_message: str

    @property
    def mouse_name(self) -> str:
        return os.path.splitext(self.yaml_name)[0].split("_")[0]

    def run_test(self, tmp_path: pathlib.Path):
        if self.error_type is None:
            subject = Subject(self.mouse_name, True, local_base_path=str(tmp_path))
            assert subject is not None

        elif issubclass(self.error_type, Warning):
            with pytest.warns(self.error_type, match=self.error_message):
                subject = Subject(self.mouse_name, True, local_base_path=str(tmp_path))

        elif issubclass(self.error_type, BaseException):
            with pytest.raises(self.error_type, match=self.error_message):
                subject = Subject(self.mouse_name, True, local_base_path=str(tmp_path))


test_cases = [
    DirectoryStructureTestCase(
        "M011_error_pca_name.yaml",
        ValueError,
        r"does not match expected pattern for PyControl .pca files",
    ),
    DirectoryStructureTestCase(
        "M015_error_number_of_pca_files.yaml",
        ValueError,
        r"Expected 2 files with extension .pca",
    ),
    DirectoryStructureTestCase(
        "M015_warn_no_task_folder.yaml",
        UserWarning,
        r"No PyControl task folder found",
    ),
    DirectoryStructureTestCase(
        "M015_error_session_date_format.yaml",
        ValueError,
        r"expected format",
    ),
    DirectoryStructureTestCase(
        "M015_error_session_folder_underscore_after_subject.yaml",
        ValueError,
        r"underscore after subject name",
    ),
    DirectoryStructureTestCase(
        "M015_error_session_folder_start_with_subject.yaml",
        ValueError,
        r"Folder name has to start with subject name",
    ),
    DirectoryStructureTestCase(
        "M015_error_two_task_py_files.yaml",
        ValueError,
        r"more than one",
    ),
    DirectoryStructureTestCase(
        "M015_error_no_task_py_file.yaml",
        FileNotFoundError,
        r"Could not find any .py files",
    ),
    DirectoryStructureTestCase(
        "M011_two_recordings.yaml",
        UserWarning,
        r"More than one raw ephys",
    ),
    DirectoryStructureTestCase(
        "M011_error_probe_folder_name.yaml",
        ValueError,
        r"doesn't match the expected format for probes",
    ),
    DirectoryStructureTestCase(
        "M011_error_not_only_probe_folders_in_ephys_recording.yaml",
        ValueError,
        r"Only folders are allowed in the ephys recordings folder",
    ),
    DirectoryStructureTestCase(
        "M011_correct.yaml",
        None,
        "",
    ),
]


@pytest.mark.parametrize("test_case", test_cases)
def test_validation(tmp_path, test_case: DirectoryStructureTestCase):
    tmp_raw_dir = tmp_path / "raw"

    def remake_raw_dir():
        if tmp_raw_dir.exists():
            shutil.rmtree(tmp_raw_dir)

        tmp_raw_dir.mkdir()

    remake_raw_dir()

    with open(os.path.join(YAML_FOLDER, test_case.yaml_name), "r") as f:
        mouse_dir_dict = YAML().load(f)

    create_directory_structure_from_dict(
        mouse_dir_dict,
        str(tmp_raw_dir),
    )

    test_case.run_test(tmp_path)