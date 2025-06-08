"""Functions for generating Markdown and JSON reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jinja2 import Template


@dataclass
class BuildReport:
    repo_name: str
    commit: str
    build_success: bool
    smoke_success: bool
    build_time: float
    env_yaml: str
    log_tail: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "commit": self.commit,
            "build_success": self.build_success,
            "smoke_success": self.smoke_success,
            "build_time": self.build_time,
            "env_yaml": self.env_yaml,
            "log_tail": self.log_tail,
        }


MD_TEMPLATE = Template(
    """# AIDAC-SCAN Report for {{ repo_name }}@{{ commit }}

- **Build success**: {{ build_success }}
- **Smoke-test success**: {{ smoke_success }}
- **Build time (s)**: {{ build_time }}

## Environment
```yaml
{{ env_yaml }}
```
{% if log_tail %}
## Log tail
```
{{ log_tail }}
```
{% endif %}
"""
)


def write_report(report: BuildReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(report.as_dict(), indent=2))
    (out_dir / "report.md").write_text(MD_TEMPLATE.render(**report.as_dict()))
