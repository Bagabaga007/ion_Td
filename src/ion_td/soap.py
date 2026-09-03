"""固定 CHNO 基和全分子平均的研究性 SOAP 描述符。"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SOAP_SPECIES = ("H", "C", "N", "O")


def read_xyz(path: str) -> tuple[list[str], np.ndarray]:
    lines = Path(path).read_text().splitlines()
    if len(lines) < 3:
        raise ValueError("XYZ 内容不足")
    try:
        count = int(lines[0])
    except ValueError as exc:
        raise ValueError("XYZ 首行必须是原子数") from exc
    symbols = []
    positions = []
    for line in lines[2 : 2 + count]:
        parts = line.split()
        if len(parts) < 4:
            continue
        symbols.append(parts[0])
        positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
    if len(symbols) != count:
        raise ValueError(f"XYZ 声明 {count} 个原子，实际读取 {len(symbols)}")
    unsupported = sorted(set(symbols) - set(SOAP_SPECIES))
    if unsupported:
        raise ValueError(f"SOAP 不支持元素: {', '.join(unsupported)}")
    return symbols, np.asarray(positions, dtype=float)


def molecular_soap(path: str) -> np.ndarray:
    try:
        from dscribe.descriptors import SOAP
    except ImportError as exc:
        raise ImportError("SOAP 需要安装 ion-td[geometry]") from exc
    from ase import Atoms

    symbols, positions = read_xyz(path)
    descriptor = SOAP(
        species=list(SOAP_SPECIES),
        periodic=False,
        r_cut=5.0,
        n_max=8,
        l_max=6,
        sigma=0.5,
        average="inner",
    )
    result = np.asarray(descriptor.create(Atoms(symbols=symbols, positions=positions)))
    if result.shape != (3696,):
        raise ValueError(f"SOAP 维度异常: {result.shape}")
    return result
