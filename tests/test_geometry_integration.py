import stat
from pathlib import Path

import pytest

import ion_td.geometry as geometry
from ion_td.geometry import XTBError, optimize_cation, resolve_xtb

pytestmark = pytest.mark.integration


def executable(path: Path, text: str) -> str:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return str(path)


SUCCESS_XTB = """#!/bin/bash
name=''
input="$1"
while [ "$#" -gt 0 ]; do
  if [ "$1" = '--namespace' ]; then name="$2"; shift 2; else shift; fi
done
cp "$input" "${name}.xtbopt.xyz"
touch ".${name}.xtboptok"
echo success
"""


def test_resolve_xtb_sources(tmp_path, monkeypatch):
    tool = executable(tmp_path / "xtb", "#!/bin/bash\nexit 0\n")
    assert resolve_xtb(tool) == str(Path(tool).resolve())
    monkeypatch.setenv("ION_TD_XTB", tool)
    assert resolve_xtb() == str(Path(tool).resolve())
    monkeypatch.delenv("ION_TD_XTB")
    monkeypatch.setattr(geometry.shutil, "which", lambda name: tool)
    assert resolve_xtb() == str(Path(tool).resolve())
    monkeypatch.setattr(geometry.shutil, "which", lambda name: None)
    with pytest.raises(XTBError, match="找不到"):
        resolve_xtb()
    nonexec = tmp_path / "nonexec"
    nonexec.write_text("x")
    with pytest.raises(XTBError, match="不可执行"):
        resolve_xtb(str(nonexec))


def test_optimize_success_and_isolation(tmp_path):
    tool = executable(tmp_path / "xtb", SUCCESS_XTB)
    output = tmp_path / "output"
    outside = tmp_path / "keep.txt"
    outside.write_text("keep")
    result = optimize_cation(
        "[NH3+]O",
        output_dir=str(output),
        name="hydroxylammonium",
        seed=42,
        xtb_executable=tool,
    )
    assert result.formal_charge == 1
    assert result.seed == 42
    assert Path(result.optimized_xyz).is_file()
    assert Path(result.stdout_log).read_text().strip() == "success"
    assert outside.read_text() == "keep"
    assert result.to_dict()["name"] == "hydroxylammonium"
    with pytest.raises(FileExistsError, match="非空"):
        optimize_cation(
            "[NH3+]O",
            output_dir=str(output),
            name="hydroxylammonium",
            xtb_executable=tool,
        )


def test_optimize_input_embedding_and_uff_branches(tmp_path, monkeypatch):
    tool = executable(tmp_path / "xtb", SUCCESS_XTB)
    with pytest.raises(ValueError, match="name"):
        optimize_cation("[NH4+]", output_dir=str(tmp_path), name="../bad", xtb_executable=tool)
    with pytest.raises(ValueError, match="无效"):
        optimize_cation("bad", output_dir=str(tmp_path), name="bad", xtb_executable=tool)

    real_embed = geometry.AllChem.EmbedMolecule
    monkeypatch.setattr(geometry.AllChem, "EmbedMolecule", lambda molecule, params: 1)
    with pytest.raises(XTBError, match="嵌入"):
        optimize_cation("[NH4+]", output_dir=str(tmp_path), name="embed", xtb_executable=tool)

    monkeypatch.setattr(geometry.AllChem, "EmbedMolecule", real_embed)
    monkeypatch.setattr(geometry.AllChem, "MMFFHasAllMoleculeParams", lambda molecule: False)
    monkeypatch.setattr(geometry.AllChem, "UFFOptimizeMolecule", lambda molecule: 0)
    result = optimize_cation(
        "[NH4+]", output_dir=str(tmp_path), name="uff", xtb_executable=tool
    )
    assert result.force_field == "UFF"


def test_optimize_process_and_artifact_failures(tmp_path, monkeypatch):
    tool = executable(tmp_path / "xtb", "#!/bin/bash\necho failed >&2\nexit 3\n")
    with pytest.raises(XTBError, match="非零状态 3"):
        optimize_cation("[NH4+]", output_dir=str(tmp_path), name="failed", xtb_executable=tool)

    missing = executable(tmp_path / "missing_xtb", "#!/bin/bash\nexit 0\n")
    with pytest.raises(XTBError, match="未产生完整"):
        optimize_cation(
            "[NH4+]", output_dir=str(tmp_path), name="missing", xtb_executable=missing
        )
