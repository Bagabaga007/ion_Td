"""确定性 RDKit 分子特征和相似度。"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, rdFingerprintGenerator

MORGAN_RADIUS = 2
MORGAN_SIZE = 512
ALLOWED_ELEMENTS = frozenset({"H", "C", "N", "O"})


@lru_cache(maxsize=1)
def descriptor_functions() -> tuple[tuple[str, object], ...]:
    return tuple(sorted(Descriptors._descList, key=lambda item: item[0]))


@lru_cache(maxsize=1)
def fingerprint_generator():
    return rdFingerprintGenerator.GetMorganGenerator(radius=MORGAN_RADIUS, fpSize=MORGAN_SIZE)


def parse_cation(smiles: str):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"无效阳离子 SMILES: {smiles!r}")
    return molecule


def formal_charge(molecule) -> int:
    return sum(atom.GetFormalCharge() for atom in molecule.GetAtoms())


def elements(molecule) -> frozenset[str]:
    return frozenset(atom.GetSymbol() for atom in molecule.GetAtoms())


def feature_vector(molecule) -> np.ndarray:
    descriptors = []
    for _, function in descriptor_functions():
        try:
            descriptors.append(float(function(molecule)))
        except (TypeError, ValueError, ZeroDivisionError):
            descriptors.append(float("nan"))
    fingerprint = fingerprint_generator().GetFingerprintAsNumPy(molecule).astype(float)
    return np.concatenate((np.asarray(descriptors, dtype=float), fingerprint))


def fingerprint(molecule):
    return fingerprint_generator().GetFingerprint(molecule)


def maximum_similarity(query, references) -> float:
    reference_list = list(references)
    if not reference_list:
        raise ValueError("相似度参考集合不能为空")
    return float(max(DataStructs.BulkTanimotoSimilarity(query, reference_list)))
