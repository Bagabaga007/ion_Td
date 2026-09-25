import json
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.config
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_preflight.py"


def _run(profile, *arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", profile, *arguments, "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_release_manifest_binds_verified_scientific_baseline_and_profile_locks():
    manifest = json.loads((ROOT / "delivery/release-manifest.json").read_text())
    assert manifest["schema_version"] == 1
    assert manifest["project"] == "ion_Td"
    assert manifest["release_status"] in {"candidate_verified", "frozen"}
    assert isinstance(manifest["source_revision"]["dirty"], bool)
    if manifest["release_status"] == "frozen":
        assert manifest["source_revision"]["dirty"] is False
    assert manifest["scientific_baseline"]["status"] == "verified"
    assert manifest["scientific_baseline"]["decision_required"] is False
    for name in ("cpu", "geometry"):
        lock = json.loads((ROOT / manifest["profiles"][name]["lock"]).read_text())
        assert lock["profile"] == name
        assert lock["version"] == manifest["version"]


def test_geometry_release_preflight_passes_independently():
    completed = _run("geometry")
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert payload["ok"] is True
    assert all(check["status"] == "PASS" for check in payload["checks"])


def test_cpu_release_preflight_passes_with_reproduced_model_card():
    completed = _run("cpu")
    payload = json.loads(completed.stdout)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert payload["ok"] is True
    assert all(check["status"] == "PASS" for check in payload["checks"])


def test_geometry_release_preflight_rejects_lock_environment_drift(tmp_path):
    manifest = json.loads((ROOT / "delivery/release-manifest.json").read_text())
    manifest["profiles"]["geometry"]["environment"]["rdkit"] = "0.0.0"
    changed = tmp_path / "release-manifest.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")
    completed = _run("geometry", "--manifest", str(changed))
    payload = json.loads(completed.stdout)
    failed = {check["id"] for check in payload["checks"] if check["status"] == "FAIL"}
    assert completed.returncode == 1
    assert "lock.geometry.environment" in failed
