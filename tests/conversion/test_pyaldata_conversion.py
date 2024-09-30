import os

import pytest
import scipy

from beneuro_data.config import _load_config
from beneuro_data.conversion.convert_nwb_to_pyaldata import convert_nwb_to_pyaldata


@pytest.mark.parametrize("session_name", ["M030_2024_04_12_09_40"])
def test_nwb_to_pyaldata(session_name):
    config = _load_config()
    subject_name = config.get_animal_name(session_name)
    local_session_path = config.get_local_session_path(session_name, 'processed')

    nwbfiles = list(local_session_path.glob('*.nwb'))
    assert nwbfiles
    assert len(nwbfiles) == 1

    # delete existing NWB file
    for nwb_file_path in local_session_path.glob("*.mat"):
        nwb_file_path.unlink()

    nwbfile_path = nwbfiles[0].absolute()

    convert_nwb_to_pyaldata(
        nwbfile_path=nwbfile_path,
        verbose=False
    )
    mat = scipy.io.loadmat(local_session_path / f'{session_name}_pyaldata.mat', simplify_cells=True)



