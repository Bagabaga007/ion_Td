import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ion_td.cli import main

pytestmark = pytest.mark.system


def executable(path: Path, text: str) -> str:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


def test_show_data_and_direct_predict(capsys, tmp_path):
    assert main(["show-data"]) == 0
    assert "records=36" in capsys.readouterr().out
    output = tmp_path / "prediction.json"
    assert main(
        [
            "predict",
            "--name",
            "hydroxylammonium",
            "--cation",
            "[NH3+]O",
            "--output",
            str(output),
        ]
    ) == 0
    payload = json.loads(output.read_text())
    assert payload["in_domain"] is True
    assert json.loads(capsys.readouterr().out)["name"] == "hydroxylammonium"


def test_config_predict_and_validate(capsys):
    root = Path(__file__).resolve().parents[1]
    assert main(["predict", "--config", str(root / "examples/prediction.yaml")]) == 0
    assert json.loads(capsys.readouterr().out)["maximum_tanimoto_similarity"] == 1.0
    assert main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["n"] == 36


def test_module_entrypoint_and_packaged_example(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    help_result = subprocess.run(
        [sys.executable, "-m", "ion_td", "--help"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "usage: ion-td" in help_result.stdout

    output = tmp_path / "prediction.json"
    example_result = subprocess.run(
        [sys.executable, str(root / "examples/run_prediction.py"), "--output", str(output)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert example_result.returncode == 0, example_result.stderr
    assert json.loads(output.read_text())["in_domain"] is True


def test_optimize_cli_with_executable_stub(tmp_path, capsys):
    tool = executable(
        tmp_path / "xtb",
        "#!/bin/bash\ninput=$1\nwhile [ $# -gt 0 ]; do "
        "if [ \"$1\" = --namespace ]; then name=$2; shift 2; else shift; fi; done\n"
        "cp \"$input\" \"${name}.xtbopt.xyz\"\ntouch \".${name}.xtboptok\"\n",
    )
    assert main(
        [
            "optimize",
            "--name",
            "ammonium",
            "--cation",
            "[NH4+]",
            "--output-dir",
            str(tmp_path / "work"),
            "--seed",
            "7",
            "--xtb",
            tool,
            "--timeout",
            "10",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["formal_charge"] == 1 and payload["seed"] == 7


def test_cli_reports_user_errors():
    with pytest.raises(SystemExit) as error:
        main(["predict"])
    assert error.value.code == 2
