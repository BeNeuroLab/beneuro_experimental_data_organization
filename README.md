![Tests](https://github.com/BeNeuroLab/beneuro_experimental_data_organization/actions/workflows/run_tests.yml/badge.svg)

This is a collection of functions for managing the experimental data recorded in the 
BeNeuro Lab, and a CLI tool called `bnd` for easy access to this functionality.

# Pipeline
The intended pipeline of use of `bnd` is as follows:

After you recorded an experimental session in the lab PCs:
```shell
# From the lab PC
$ bnd up MXX  # Uploads latest session of animal MXX to RDS
```
On your local PC:
```shell
$ bnd dl MXX  # Download latest session of animal MXX from RDS to local PC
$ bnd kilosort-session <local/path/to/session> MXX  # Kilosorts session and saves in local processed
$ bnd to-nwb <local/path/to/session> MXX  # Converts data to .nwb format
$ bnd nwb-to-pyaldata MXX_2024_01_01_09_00  # Convert session into pyaldata format
```
# Setting up
## Installation
1. You will need the environment management tool [poetry](https://python-poetry.org). We 
   recommend using the official installer:
    - On Linux, MacOS or WSL:`curl -sSL https://install.python-poetry.org | python3 -`
    - On Windows Powershell: `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -`
   
2. Clone this repo:`git clone https://github.com/BeNeuroLab/beneuro_experimental_data_organization.git`

3. Navigate into the folder you just downloaded (`beneuro_experimental_data_organization`)
4. Create the enviroment associated to the project:

     `poetry shell`

    This will generate a virtualenv where you install all the packages needed for `bnd` 
   and activate it
5. Install the package with either

     `poetry install`

   or if you want spike sorting functionality:

     `poetry install --with processing`

   For more info, see the [spike sorting instructions](#spike-sorting).

6. Test that the install worked with

     `poetry run pytest`

   Hopefully you'll see green on the bottom (some yellow is fine) meaning that all tests pass :)


> Note:
>
> If you want to make the environment activation a bit more straightforward instead of 
> navigating to the folder and running `poetry shell` you can make an alias in your 
> terminal app:
> - Windows:


## Configuring the local and remote data storage
The tool needs to know where the experimental data is stored locally and remotely.

0. Mount the RDS server. (If you're able to access the data on it from the file browser, it's probably already mounted.)

1. Run `bnd init` and enter the root folders where the experimental data are stored on the local computer and the server. These refer to the folders where you have `raw` and `processed` folders.

   This will create a file called `.env` in the `beneuro_experimental_data_organization` folder and add the following content:
   ```
   LOCAL_PATH = /path/to/the/root/of/the/experimental/data/storage/on/the/local/computer
   REMOTE_PATH = /path/to/the/root/of/the/experimental/data/storage/where/you/mounted/RDS/to
   ```

   Alternatively, you can create this file by hand.

2. Run `bnd check-config` to verify that the folders in the config have the expected `raw` and `processed` folders within them.


# Usage
## Help
- To see the available commands: `bnd --help`
- To see the help of a command (e.g. `rename-videos`): `bnd rename-videos --help`

## Uploading the data
Once you're done recording a session, you can upload that session to the server with:
  
  `bnd upload-session . <subject-name>`

or if you don't want to `cd` into the session's directory:

  `bnd upload-last <subject-name>`

This should first rename the videos and extra files (unless otherwise specified), validate the data, then copy it to the server, and complain if it's already there.

## Downloading data from the server
Downloading data to your local computer is similar to uploading, but instead of throwing errors, missing or invalid data is handled by skipping it and warning about it.

Using the session's path, e.g. after navigating to the session's folder on RDS mounted to your computer:

  `bnd download-session . <subject-name>`

or just the last session of a subject:

  `bnd download-last <subject-name>`

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

## Data validation
- You can validate the structure of raw data for an individual session:
  - `bnd validate-session . <subject-name>` if you're in the session's directory
  - `bnd validate-session /absolute/path/to/session/folder <subject-name>` from anywhere
  - `bnd validate-last <subject-name>` from anywhere to validate the last recorded session
  - `bnd validate-today` from anywhere to validate all recorded sessions on the current day
    - If it's trying to validate things in places like "treadmill-calibration" that are on the same level as subject directories, you can exclude checking in those places
    by adding them to `IGNORED_SUBJECT_LEVEL_DIRS` in the `.env` config file (`IGNORED_SUBJECT_LEVEL_DIRS = ["treadmill-calibration", "other-stuff-you-want-to-ignore"]`)
    - `bnd list-today` lets you check what sessions were recorded on the current day
 
  This will give you an error if there is a problem with the file structure.

  The name of the subject is used for confirmation, but might be removed in the future if it's too annoying.

- or for all sessions of a subject:
  - `bnd validate-sessions <subject-name>`
 
  This will give you an overview which sessions look good and which ones have a problem.

By default behavioral, ephys, and video data are all checked. To control which kind of data you want to check:
- To exclude checking something: `--ignore-behavior`, `--ignore-ephys`, `--ignore-videos`
- To explicitly include something: `--check-behavior`, `--check-ephys`, `--check-videos`

Please note that running validation will only give you the first problem that pops up. Once you fixed that, run it again to see if there are others ;)
 
## Renaming the videos
The default naming Jarvis uses for the video folder and files doesn't match the convention we want to follow.

Files can be renamed with `bnd rename-videos . <subject-name>` (or specifying the path instead of `.` if the current working directory is not the session's directory).

Add `--verbose` to the end to see what files were renamed.

## Renaming the extra files
Sometimes the experimenter leaves comments in a `comment.txt` file or saves some extra `.txt` files in the electrophysiology recording folders.

To rename these files to follow the naming convention of `<session-name>_<filename>`, you can use the `bnd rename-extra-files` command.



# Please file an issue if something doesn't work or is just annoying to use!
