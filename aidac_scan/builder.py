"""Utilities for building and testing repositories in isolated environments."""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Tuple

from git import Repo


def clone_repo(url: str, dest: Path | None = None) -> Path:
    """Clone the git repository into a temporary directory."""
    dest = dest or Path(tempfile.mkdtemp(prefix="aidac_repo_"))
    Repo.clone_from(url, dest)
    return dest


def repo_info(path: Path) -> Tuple[str, str]:
    """Return repository name and current commit hash."""
    repo = Repo(path)
    return Path(repo.working_dir).name, repo.head.commit.hexsha


def generate_env_yaml(repo_path: Path) -> str:
    """Generate a simple conda environment YAML from requirements.txt."""
    req = repo_path / "requirements.txt"
    lines = [
        "name: aidac_env",
        "channels:",
        "  - conda-forge",
        "dependencies:",
        "  - python=3.10",
        "  - pip",
    ]
    if req.exists():
        lines.append("  - pip:")
        lines.append("      - -r requirements.txt")
    return "\n".join(lines) + "\n"


def build_environment(env_yaml: str, repo_path: Path) -> Tuple[bool, str, float, str]:
    """Create the environment and install the repo."""
    env_file = repo_path / "env_generated.yaml"
    env_file.write_text(env_yaml)
    env_name = f"aidac_env_{int(time.time())}"
    start = time.time()
    try:
        create_proc = subprocess.run(
            ["micromamba", "create", "-y", "-n", env_name, "-f", str(env_file)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        return False, str(e), time.time() - start, env_name
    logs = create_proc.stdout + create_proc.stderr
    if create_proc.returncode != 0:
        return False, logs, time.time() - start, env_name

    install_proc = subprocess.run(
        ["micromamba", "run", "-n", env_name, "pip", "install", "-e", "."],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    logs += install_proc.stdout + install_proc.stderr
    success = install_proc.returncode == 0
    return success, logs, time.time() - start, env_name


def run_smoke_test(env_name: str, repo_path: Path) -> Tuple[bool, str]:
    """Run pytest if tests exist, otherwise pip list."""
    tests_exist = (repo_path / "tests").exists()
    if tests_exist:
        cmd = [
            "micromamba",
            "run",
            "-n",
            env_name,
            "python",
            "-m",
            "pytest",
            "-q",
        ]
    else:
        cmd = [
            "micromamba",
            "run",
            "-n",
            env_name,
            "python",
            "-m",
            "pip",
            "list",
        ]
    try:
        proc = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        log = proc.stdout + proc.stderr
        return proc.returncode == 0, log
    except FileNotFoundError as e:
        return False, str(e)
