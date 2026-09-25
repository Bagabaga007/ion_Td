#!/usr/bin/env python3
"""Verify ion_Td CPU and xTB/geometry release profiles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "delivery" / "release-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(paths: list[str]) -> tuple[str, int]:
    files: set[Path] = set()
    for pattern in paths:
        files.update(path for path in ROOT.glob(pattern) if path.is_file())
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(f"{sha256(path)}  {relative}\n".encode())
    return digest.hexdigest(), len(files)


def add_check(report: dict[str, Any], check_id: str, ok: bool, detail: str) -> None:
    report["checks"].append(
        {"id": check_id, "status": "PASS" if ok else "FAIL", "detail": detail}
    )
    report["ok"] = report["ok"] and ok


def validate_common(report: dict[str, Any], manifest: dict[str, Any], profile: str) -> None:
    add_check(report, "manifest.schema", manifest.get("schema_version") == 1, "schema_version=1")
    add_check(report, "manifest.project", manifest.get("project") == "ion_Td", "project=ion_Td")
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]
    add_check(
        report,
        "project.version",
        project_version == manifest.get("version"),
        f"pyproject={project_version}; manifest={manifest.get('version')}",
    )

    tree = manifest["source_revision"]["trees"][profile]
    actual_tree, count = tree_sha256(tree["paths"])
    add_check(
        report,
        f"source.{profile}",
        actual_tree == tree["sha256"] and count == tree["file_count"],
        f"sha256={actual_tree}; files={count}",
    )
    lock_path = ROOT / manifest["profiles"][profile]["lock"]
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    add_check(
        report,
        f"lock.{profile}.identity",
        lock.get("project") == "ion_Td"
        and lock.get("profile") == profile
        and lock.get("version") == manifest.get("version")
        and lock.get("source_tree_sha256") == tree["sha256"],
        f"lock={lock_path}",
    )
    add_check(
        report,
        f"lock.{profile}.environment",
        lock.get("python") == manifest["profiles"][profile].get("python")
        and lock.get("environment") == manifest["profiles"][profile].get("environment")
        and platform.python_version() == lock.get("python"),
        f"actual_python={platform.python_version()}; expected_python={lock.get('python')}",
    )
    if profile == "cpu":
        artifacts = {item["path"]: item for item in manifest["artifacts"]}
        add_check(
            report,
            "lock.cpu.scientific_assets",
            lock.get("training", {}).get("sha256")
            == artifacts["src/ion_td/data/training.csv"]["sha256"]
            and lock.get("model_card", {}).get("sha256")
            == artifacts["src/ion_td/data/model_card.json"]["sha256"]
            and lock.get("live_loo") == manifest["scientific_baseline"]["live_loo"],
            "training, model card and live LOO agree with the manifest",
        )
    else:
        add_check(
            report,
            "lock.geometry.xtb",
            lock.get("xtb") == manifest["profiles"]["geometry"].get("xtb"),
            "xTB executable identity agrees with the manifest",
        )
    for artifact in manifest["artifacts"]:
        if profile not in artifact["profiles"]:
            continue
        path = ROOT / artifact["path"]
        exists = path.is_file()
        actual_hash = sha256(path) if exists else None
        actual_size = path.stat().st_size if exists else None
        ok = exists and actual_hash == artifact["sha256"] and actual_size == artifact["size_bytes"]
        if artifact["required"]:
            add_check(
                report,
                f"artifact.{artifact['path']}",
                ok,
                f"sha256={actual_hash}; size_bytes={actual_size}",
            )


def _installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def validate_dependencies(report: dict[str, Any], dependencies: dict[str, str]) -> None:
    for distribution, expected in dependencies.items():
        actual = _installed_version(distribution)
        add_check(
            report,
            f"environment.{distribution}",
            actual == expected,
            f"actual={actual}; expected={expected}",
        )


def validate_cpu(report: dict[str, Any], manifest: dict[str, Any]) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from ion_td import __version__
    from ion_td.dataset import load_training_records
    from ion_td.model import predict_temperature, validate_model

    profile = manifest["profiles"]["cpu"]
    add_check(
        report,
        "cpu.package_version",
        __version__ == manifest["version"],
        f"ion_td.__version__={__version__}",
    )
    validate_dependencies(report, profile["environment"])
    records = load_training_records()
    add_check(
        report,
        "cpu.training_records",
        len(records) == profile["training_records"],
        f"records={len(records)}",
    )
    live = validate_model().__dict__
    card = json.loads((ROOT / "src/ion_td/data/model_card.json").read_text(encoding="utf-8"))
    tolerance = float(profile["validation_absolute_tolerance"])
    mismatches = {
        key: {"live": live[key], "model_card": card["validation"][key]}
        for key in live
        if abs(float(live[key]) - float(card["validation"][key])) > tolerance
    }
    add_check(
        report,
        "cpu.model_card_live_loo",
        not mismatches,
        "model card matches live LOO" if not mismatches else json.dumps(mismatches, sort_keys=True),
    )
    baseline = manifest["scientific_baseline"]
    expected_live = baseline["live_loo"]
    live_locked = all(
        abs(float(live[key]) - float(expected_live[key])) <= tolerance for key in live
    )
    add_check(
        report,
        "cpu.live_loo_lock",
        live_locked,
        json.dumps(live, sort_keys=True),
    )
    prediction = predict_temperature("[NH3+]O", name="release-preflight")
    add_check(
        report,
        "cpu.prediction_smoke",
        prediction.in_domain and prediction.model_version == card["model_version"],
        f"temperature_c={prediction.temperature_c:.12f}; model={prediction.model_version}",
    )


def validate_geometry(
    report: dict[str, Any], manifest: dict[str, Any], xtb_path: str | None, smoke: str
) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from ion_td.geometry import optimize_cation, resolve_xtb

    profile = manifest["profiles"]["geometry"]
    validate_dependencies(report, profile["environment"])
    try:
        resolved = Path(resolve_xtb(xtb_path or profile["xtb"]["path"]))
    except Exception as exc:
        add_check(report, "geometry.xtb_visibility", False, f"{type(exc).__name__}: {exc}")
        return
    add_check(report, "geometry.xtb_visibility", True, str(resolved))
    actual_hash = sha256(resolved)
    add_check(
        report,
        "geometry.xtb_sha256",
        actual_hash == profile["xtb"]["sha256"],
        f"actual={actual_hash}; expected={profile['xtb']['sha256']}",
    )
    completed = subprocess.run(
        [str(resolved), "--version"], text=True, capture_output=True, timeout=30, check=False
    )
    version_text = f"{completed.stdout}\n{completed.stderr}"
    add_check(
        report,
        "geometry.xtb_version",
        completed.returncode == 0 and profile["xtb"]["version"] in version_text,
        f"returncode={completed.returncode}; expected={profile['xtb']['version']}",
    )
    if smoke == "run" and report["ok"]:
        with tempfile.TemporaryDirectory(prefix="ion_td_release_preflight_") as temp_dir:
            result = optimize_cation(
                "[NH3+]O",
                output_dir=temp_dir,
                name="hydroxylammonium",
                seed=profile["smoke"]["seed"],
                xtb_executable=str(resolved),
                timeout=profile["smoke"]["timeout_seconds"],
            )
            optimized = Path(result.optimized_xyz)
            ok = result.formal_charge == 1 and optimized.is_file() and optimized.stat().st_size > 0
            add_check(
                report,
                "geometry.optimization_smoke",
                ok,
                f"formal_charge={result.formal_charge}; force_field={result.force_field}; output_nonempty={optimized.stat().st_size > 0}",
            )


def run(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "project": "ion_Td",
        "version": manifest.get("version"),
        "profile": args.profile,
        "manifest": str(manifest_path),
        "release_status": manifest.get("release_status"),
        "ok": True,
        "checks": [],
    }
    profiles = ["cpu", "geometry"] if args.profile == "all" else [args.profile]
    for profile in profiles:
        validate_common(report, manifest, profile)
        if profile == "cpu":
            validate_cpu(report, manifest)
        else:
            validate_geometry(report, manifest, args.xtb, args.geometry_smoke)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify ion_Td release locks")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--profile", choices=("cpu", "geometry", "all"), default="all")
    parser.add_argument("--xtb", help="xTB executable; defaults to the manifest-pinned path")
    parser.add_argument(
        "--geometry-smoke",
        choices=("visibility", "run"),
        default="visibility",
        help="Use run for a bounded real RDKit→xTB optimization smoke test",
    )
    parser.add_argument("--json", action="store_true", help="Emit one machine-readable JSON document")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:
        report = {
            "project": "ion_Td",
            "profile": args.profile,
            "ok": False,
            "checks": [
                {"id": "preflight.internal", "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"}
            ],
        }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for check in report["checks"]:
            print(f"[{check['status']}] {check['id']}: {check['detail']}")
        print("PASS" if report["ok"] else "FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
