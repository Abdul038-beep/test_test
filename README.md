# AIDAC-SCAN

A minimal prototype CLI that clones a GitHub repository, builds a conda environment using `micromamba`, runs a smoke test, and produces a reproducibility report.

## Installation

```bash
pip install -e .
```

## Usage

```bash
aidac-scan <repo-url> --output my_report
```

The tool will generate `report.md` and `report.json` inside the output directory.
