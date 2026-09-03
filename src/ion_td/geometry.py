"""确定性阳离子几何生成和隔离 xTB 优化。"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem

_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


class XTBError(RuntimeError):
    """xTB 执行或工件验证失败。"""


@dataclass(frozen=True)
class OptimizationResult:
    name: str
    formal_charge: int
    seed: int
    force_field: str
    force_field_status: int
    input_xyz: str
    optimized_xyz: str
    stdout_log: str
    stderr_log: str
    xtb_executable: str

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_xtb(explicit: str | None = None) -> str:
    candidate = explicit or os.environ.get("ION_TD_XTB") or shutil.which("xtb")
    if not candidate:
        raise XTBError("找不到 xTB；请用 --xtb 或 ION_TD_XTB 指定可执行文件")
    path = Path(candidate).expanduser().resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise XTBError(f"xTB 不可执行: {path}")
    return str(path)


def _write_rdkit_xyz(molecule, path: Path) -> None:
    conformer = molecule.GetConformer()
    lines = [str(molecule.GetNumAtoms()), "ion_Td deterministic RDKit geometry"]
    for atom in molecule.GetAtoms():
        position = conformer.GetAtomPosition(atom.GetIdx())
        lines.append(
            f"{atom.GetSymbol():<3} {position.x: .10f} {position.y: .10f} {position.z: .10f}"
        )
    path.write_text("\n".join(lines) + "\n")


def optimize_cation(
    cation_smiles: str,
    *,
    output_dir: str,
    name: str,
    seed: int = 20260903,
    xtb_executable: str | None = None,
    timeout: int = 600,
) -> OptimizationResult:
    if not _SAFE_NAME.fullmatch(name):
        raise ValueError("name 只能包含字母、数字、点、下划线和连字符")
    molecule = Chem.MolFromSmiles(cation_smiles)
    if molecule is None:
        raise ValueError(f"无效阳离子 SMILES: {cation_smiles!r}")
    molecule = Chem.AddHs(molecule)
    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = int(seed)
    if AllChem.EmbedMolecule(molecule, parameters) != 0:
        raise XTBError("RDKit 三维嵌入失败")
    if AllChem.MMFFHasAllMoleculeParams(molecule):
        force_field = "MMFF"
        force_field_status = int(AllChem.MMFFOptimizeMolecule(molecule))
    else:
        force_field = "UFF"
        force_field_status = int(AllChem.UFFOptimizeMolecule(molecule))

    target = Path(output_dir) / name
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"输出目录非空: {target}")
    target.mkdir(parents=True, exist_ok=True)
    input_xyz = target / f"{name}.xyz"
    _write_rdkit_xyz(molecule, input_xyz)
    charge = sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())
    executable = resolve_xtb(xtb_executable)
    command = [
        executable,
        input_xyz.name,
        "--opt",
        "loose",
        "--gfn",
        "2",
        "--chrg",
        str(charge),
        "--namespace",
        name,
    ]
    completed = subprocess.run(
        command,
        cwd=target,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout_log = target / "stdout.log"
    stderr_log = target / "stderr.log"
    stdout_log.write_text(completed.stdout or "")
    stderr_log.write_text(completed.stderr or "")
    optimized_xyz = target / f"{name}.xtbopt.xyz"
    marker = target / f".{name}.xtboptok"
    if completed.returncode != 0:
        raise XTBError(f"xTB 返回非零状态 {completed.returncode}; 见 {stderr_log}")
    if not marker.exists() or not optimized_xyz.is_file() or optimized_xyz.stat().st_size == 0:
        raise XTBError("xTB 未产生完整优化 marker/XYZ")
    return OptimizationResult(
        name=name,
        formal_charge=charge,
        seed=int(seed),
        force_field=force_field,
        force_field_status=force_field_status,
        input_xyz=str(input_xyz.resolve()),
        optimized_xyz=str(optimized_xyz.resolve()),
        stdout_log=str(stdout_log.resolve()),
        stderr_log=str(stderr_log.resolve()),
        xtb_executable=executable,
    )
