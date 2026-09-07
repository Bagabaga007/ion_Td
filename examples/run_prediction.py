"""Run the packaged ion_Td prediction example.

Usage from the repository root after ``pip install -e .``::

    python examples/run_prediction.py
    python examples/run_prediction.py --output work/prediction.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ion_td.cli import main as cli_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the offline ion_Td prediction example")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("prediction.yaml")),
        help="YAML prediction config (default: this directory/prediction.yaml)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="optional JSON output path passed to ion-td",
    )
    args = parser.parse_args()
    command = ["predict", "--config", args.config]
    if args.output:
        command.extend(["--output", args.output])
    return cli_main(command)


if __name__ == "__main__":
    raise SystemExit(main())
