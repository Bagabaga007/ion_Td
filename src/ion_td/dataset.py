"""训练数据读取、校验与固定五唑盐适用域。"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from importlib.resources import files
from typing import Iterable

from rdkit import Chem

PENTAZOLATE_SMILES = "N1=NN=N[N-]1"
REQUIRED_COLUMNS = (
    "Tdec",
    "Reference",
    "ID",
    "SMILES_cation",
    "SMILES_anion",
    "SMILES",
)


@dataclass(frozen=True)
class TrainingRecord:
    identifier: str
    tdec_c: float
    reference: str
    cation_smiles: str
    anion_smiles: str
    salt_smiles: str


def canonical_smiles(smiles: str) -> str:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"无效 SMILES: {smiles!r}")
    return Chem.MolToSmiles(molecule, canonical=True)


def _validate_records(records: Iterable[TrainingRecord]) -> tuple[TrainingRecord, ...]:
    result = tuple(records)
    if not result:
        raise ValueError("训练数据不能为空")
    identifiers = [record.identifier for record in result]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("训练数据 ID 必须唯一")
    expected_anion = canonical_smiles(PENTAZOLATE_SMILES)
    for record in result:
        if not math.isfinite(record.tdec_c):
            raise ValueError(f"{record.identifier}: Tdec 必须是有限数值")
        if canonical_smiles(record.anion_smiles) != expected_anion:
            raise ValueError(f"{record.identifier}: 训练集包含非五唑阴离子")
        cation = Chem.MolFromSmiles(record.cation_smiles)
        if cation is None:
            raise ValueError(f"{record.identifier}: 阳离子 SMILES 无效")
        charge = sum(atom.GetFormalCharge() for atom in cation.GetAtoms())
        if charge != 1:
            raise ValueError(f"{record.identifier}: 阳离子形式电荷应为 +1，实际 {charge:+d}")
    return result


def load_training_records() -> tuple[TrainingRecord, ...]:
    resource = files("ion_td").joinpath("data", "training.csv")
    with resource.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError(f"训练数据列不匹配: {reader.fieldnames}")
        records = [
            TrainingRecord(
                identifier=row["ID"],
                tdec_c=float(row["Tdec"]),
                reference=row["Reference"],
                cation_smiles=row["SMILES_cation"],
                anion_smiles=row["SMILES_anion"],
                salt_smiles=row["SMILES"],
            )
            for row in reader
        ]
    return _validate_records(records)
