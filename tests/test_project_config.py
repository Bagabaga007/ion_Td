import hashlib
import json
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest

from ion_td.model import validate_model

pytestmark = pytest.mark.config


def test_pyproject_and_manifest_contract():
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)
    assert project["project"]["name"] == "ion-td"
    assert project["tool"]["coverage"]["run"]["branch"] is True
    assert project["tool"]["coverage"]["report"]["fail_under"] == 100
    assert "recursive-include tests *.py" in (root / "MANIFEST.in").read_text()
    assert "recursive-include examples" in (root / "MANIFEST.in").read_text()


def test_operable_example_contract():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/usage.md").is_file()
    assert (root / "examples/README.md").is_file()
    assert (root / "examples/run_prediction.py").is_file()
    assert "ion-td optimize" in (root / "docs/usage.md").read_text()
    assert "maximum_tanimoto_similarity" in (root / "examples/README.md").read_text()


def test_training_and_source_manifest_hashes():
    data = files("ion_td").joinpath("data")
    training = data.joinpath("training.csv").read_bytes()
    manifest = json.loads(data.joinpath("source_manifest.json").read_text())
    assert hashlib.sha256(training).hexdigest() == manifest["sha256"]
    assert manifest["records"] == 36
    assert "salt36" in manifest["correction"]


def test_model_card_matches_live_leave_one_out():
    data = files("ion_td").joinpath("data")
    card = json.loads(data.joinpath("model_card.json").read_text())
    live = validate_model()
    assert live.__dict__ == pytest.approx(card["validation"], abs=1e-12)
