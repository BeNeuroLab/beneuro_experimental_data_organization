![Tests](https://github.com/BeNeuroLab/beneuro_experimental_data_organization/actions/workflows/run_tests.yml/badge.svg)

This is a collection of functions for managing the experimental data recorded in the 
BeNeuro Lab, and a CLI tool called `bnd` for easy access to this functionality.
# Setting up
## Installation (user)
If you just want to use bnd without the hassle of going through poetry we can do this 
with conda
1. Install `conda`
   - You can use either [Miniconda](https://docs.anaconda.com/miniconda/install/#quick-command-line-install) or [Miniforge](https://github.com/conda-forge/miniforge)
2. Clone repo
   ```shell
   git clone https://github.com/BeNeuroLab/beneuro_experimental_data_organization.git
   cd ./beneuro_experimental_data_organization
   ```
3. Open either Miniconda prompt or Miniforge promt and run the following command. This 
   may take some time: 
   ```shell
   conda env create --file=environment.yml
   ```
4. Create your configuration file:
   ```shell
   bnd init  # Provide the path to the repo, and to local and remote data storage
   bnd --help # Start reading about the functions!
   ```

# Pipeline
The intended pipeline of use of `bnd` is as follows:

After you recorded an experimental session in the lab PCs:
```shell
# From the lab PC
$ bnd up MXX -b -e -v  # Uploads latest behaviour ephys and videos session of animal MXX to RDS
```
On your local PC:
```shell
$ bnd dl MXX_2024_01_01_09_00  # Download latest session of animal MXX from RDS to local PC
$ bnd to-pyal MXX_2024_01_01_09_00 -k # Convert session into pyaldata format. Kilosorts and converts to nwb before
$ bnd up MXX_2024_01_01_09_00 -n -p  # Still pending. Uploads nwb and pyaldata to rds
```

# CLI usage
## Help
- To see the available commands: `bnd --help`
- To see the help of a command (e.g. `rename-videos`): `bnd up --help`

## Uploading the data
Once you're done recording a session, you can upload that session to the server with:
  
  `bnd up <subject-name-or-session-name>`

This should first rename the videos and extra files (unless otherwise specified), validate the data, then copy it to the server, and complain if it's already there.
You can specify different data options:
```text
| --include-behavior         -b  --ignore-behavior         -B    Upload behavioral data (-b) or not (-B).              |
│                                                                [default: ignore-behavior]                            │
│ --include-ephys            -e  --ignore-ephys            -E    Upload ephys data (-e) or not (-E).                   │
│                                                                [default: ignore-ephys]                               │
│ --include-videos           -v  --ignore-videos           -V    Upload video data (-v) or not (-V).                   │
│                                                                [default: ignore-videos]                              │
│ --include-nwb              -n  --ignore-nwb              -N    Upload NWB files (-n) or not (-N).                    │
│                                                                [default: ignore-nwb]                                 │
│ --include-pyaldata         -p  --ignore-pyaldata         -P    Upload PyalData files (-p) or not (-P).               │
│                                                                [default: ignore-pyaldata]                            │
│ --include-kilosort-output  -k  --ignore-kilosort-output  -K    Upload Kilosort output (-k) or not (-K).              │
│                                                                [default: ignore-kilosort-output] 
```

If will skip a data type if its already present in RDS

## Downloading data from the server
Downloading data to your local computer is similar to uploading, but instead of throwing errors, missing or invalid data is handled by skipping it and warning about it.

Using the session's path assuming you have RDS mounted to your computer:

  `bnd dl <subject-name-or-session-name>`

## Pyaldata conversion

## Spike sorting
Currently we are using Kilosort 4 for spike sorting, and provide a command to run sorting on a session and save the results in the processed folder.

Note that you will need some extra dependencies that are not installed by default, and that this will most likely only work on Linux.<br>
You can install the spike sorting dependencies by running `poetry install --with processing` in bnd's root folder.

You will also need docker to run the pre-packaged Kilosort docker images and the nvidia-container-toolkit to allow those images to use the GPU.<br>
If not already installed, install docker following the instructions [on this page](https://docs.docker.com/engine/install/ubuntu/), then install nvidia-container-toolkit following [these instructions](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).


Basic usage:

  `bnd kilosort-session . M020`

Only sorting specific probes:

  `bnd kilosort-session . M020 imec0`

  `bnd kilosort-session . M020 imec0 imec1`

Keeping binary files useful for Phy:

  `bnd kilosort-session . M020 --keep-temp-files`

Suppressing output:

  `bnd kilosort-session . M020 --no-verbose`

# Please file an issue if something doesn't work or is just annoying to use!

Notes from nvidia debugging:
check
nvidia-smi

if it fails:
sudo apt-get purge nvidia*
sudo ubuntu-drivers autoinstall
sudo reboot

purge container toolking
sudo apt-get purge nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
