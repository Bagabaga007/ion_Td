"""预测配置加载。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .dataset import PENTAZOLATE_SMILES


@dataclass(frozen=True)
class PredictionConfig:
    name: str
    cation_smiles: str
    anion_smiles: str = PENTAZOLATE_SMILES
    allow_out_of_domain: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "PredictionConfig":
        smiles = data.get("SMILES", {})
        cation = data.get("cation_smiles", smiles.get("cation"))
        anion = data.get("anion_smiles", smiles.get("anion")) or PENTAZOLATE_SMILES
        name = data.get("name")
        if not name or not cation:
            raise ValueError("配置必须提供 name 和 cation_smiles/SMILES.cation")
        return cls(
            name=str(name),
            cation_smiles=str(cation),
            anion_smiles=str(anion),
            allow_out_of_domain=bool(data.get("allow_out_of_domain", False)),
        )


def load_config(path: str) -> PredictionConfig:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("配置根节点必须是映射")
    return PredictionConfig.from_mapping(data)
