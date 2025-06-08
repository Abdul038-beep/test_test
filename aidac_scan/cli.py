"""Command line interface for AIDAC-SCAN."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.progress import Progress

from aidac_scan.builder import (
    build_environment,
    clone_repo,
    generate_env_yaml,
    repo_info,
    run_smoke_test,
)
from aidac_scan.report import BuildReport, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AIDAC-SCAN on a repo")
    parser.add_argument("repo", help="Git repository URL")
    parser.add_argument(
        "--dataset", help="Optional dataset path", default=None
    )
    parser.add_argument(
        "--output", help="Output directory for report", default="aidac_output"
    )
    args = parser.parse_args(argv)

    repo_path = clone_repo(args.repo)
    name, commit = repo_info(repo_path)
    env_yaml = generate_env_yaml(repo_path)

    with Progress() as progress:
        task = progress.add_task("Building environment", total=None)
        success, logs, duration, env_name = build_environment(env_yaml, repo_path)
        progress.remove_task(task)

    log_tail = "\n".join(logs.strip().splitlines()[-50:]) if not success else ""
    if not success:
        log_dir = Path(args.output) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "build_fail.log").write_text(log_tail)
        write_report(
            BuildReport(
                repo_name=name,
                commit=commit,
                build_success=False,
                smoke_success=False,
                build_time=duration,
                env_yaml=env_yaml,
                log_tail=log_tail,
            ),
            Path(args.output),
        )
        return 1

    smoke_success, smoke_log = run_smoke_test(env_name, repo_path)

    write_report(
        BuildReport(
            repo_name=name,
            commit=commit,
            build_success=True,
            smoke_success=smoke_success,
            build_time=duration,
            env_yaml=env_yaml,
            log_tail="" if smoke_success else smoke_log.splitlines()[-50:],
        ),
        Path(args.output),
    )
    return 0 if smoke_success else 1


if __name__ == "__main__":
    sys.exit(main())
