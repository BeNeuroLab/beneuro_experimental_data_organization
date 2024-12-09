from pathlib import Path

import pytest

from beneuro_data.conversion.anipose_interface import AniposeInterface

TEST_DIR_PATH = Path(__file__).parent.parent


@pytest.mark.processing
@pytest.mark.parametrize("csv_name", ["M030_2024_04_12_09_40_3dpts_angles.csv"])
def test_anipose_csv_loading(csv_name):
    csv_path = TEST_DIR_PATH / "test_data" / csv_name
    print(type(csv_path))

    interface = AniposeInterface(csv_path)

    for kp_name in AniposeInterface.keypoint_names:
        for postfix in ["x", "y", "z"]:
            assert f"{kp_name}_{postfix}" in interface.pose_data.columns

    for angle_name, _ in AniposeInterface.angle_names_and_references:
        assert angle_name in interface.pose_data.columns
