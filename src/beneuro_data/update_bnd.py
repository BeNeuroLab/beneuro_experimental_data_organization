import subprocess
from pathlib import Path

from rich import print


def _run_git_command(repo_path: str, command: list[str]) -> str:
    """Run a git command in the specified repository and return its output"""
    result = subprocess.run(
        ["git", "-C", repo_path] + command, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout.strip()


def _get_new_commits(repo_path: str) -> list[str]:
    """Check for new commits from origin/main"""
    # Fetch the latest changes from the remote repository
    _run_git_command(repo_path, ["fetch"])

    # Check if origin/main has new commits compared to the local branch
    new_commits = _run_git_command(repo_path, ["log", "HEAD..origin/main", "--oneline"])

    return new_commits.split("\n")


def update_bnd(print_new_commits: bool = False):
    package_path = Path(__file__).absolute().parent.parent.parent

    new_commits = _get_new_commits(package_path)

    if len(new_commits) > 0:
        print("New commits found, pulling changes...")
        _run_git_command(package_path, ["pull", "origin", "main"])
        print("Package updated successfully.")

        if print_new_commits:
            print("New commits:")
            for commit in new_commits:
                print(f" - {commit}")
    else:
        print("Package appears to be up to date, no new commits found.")
