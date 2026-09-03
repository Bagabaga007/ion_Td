"""确定性模型、适用域与不确定性输出。"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline

from .dataset import PENTAZOLATE_SMILES, canonical_smiles, load_training_records
from .features import (
    ALLOWED_ELEMENTS,
    elements,
    feature_vector,
    fingerprint,
    formal_charge,
    maximum_similarity,
    parse_cation,
)


class ApplicabilityError(ValueError):
    """输入超出模型声明的训练域。"""


@dataclass(frozen=True)
class ValidationResult:
    n: int
    r2: float
    mae_c: float
    rmse_c: float
    conformal_half_width_c: float


@dataclass(frozen=True)
class PredictionResult:
    name: str
    temperature_c: float
    interval_low_c: float
    interval_high_c: float
    tree_std_c: float
    maximum_tanimoto_similarity: float
    in_domain: bool
    warnings: tuple[str, ...]
    model_version: str
    validation: ValidationResult

    def to_dict(self) -> dict:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result


@dataclass
class _Bundle:
    model: Pipeline
    training_fingerprints: tuple
    validation: ValidationResult
    model_card: dict


def _new_model() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer()),
            ("variance", VarianceThreshold(1e-14)),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=500,
                    random_state=42,
                    max_features=0.5,
                    min_samples_leaf=2,
                    n_jobs=1,
                ),
            ),
        ]
    )


def _training_arrays():
    records = load_training_records()
    molecules = tuple(parse_cation(record.cation_smiles) for record in records)
    matrix = np.vstack([feature_vector(molecule) for molecule in molecules])
    target = np.asarray([record.tdec_c for record in records], dtype=float)
    return records, molecules, matrix, target


def _conformal_half_width(residuals: np.ndarray, coverage: float = 0.90) -> float:
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage 必须位于 (0, 1)")
    rank = math.ceil((len(residuals) + 1) * coverage)
    return float(np.sort(residuals)[min(rank - 1, len(residuals) - 1)])


@lru_cache(maxsize=1)
def validate_model() -> ValidationResult:
    _, _, matrix, target = _training_arrays()
    predictions = cross_val_predict(
        _new_model(), matrix, target, cv=LeaveOneOut(), n_jobs=1
    )
    residuals = np.abs(target - predictions)
    return ValidationResult(
        n=len(target),
        r2=float(r2_score(target, predictions)),
        mae_c=float(mean_absolute_error(target, predictions)),
        rmse_c=float(math.sqrt(mean_squared_error(target, predictions))),
        conformal_half_width_c=_conformal_half_width(residuals),
    )


def _load_model_card() -> dict:
    resource = files("ion_td").joinpath("data", "model_card.json")
    return json.loads(resource.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _bundle() -> _Bundle:
    _, molecules, matrix, target = _training_arrays()
    model = _new_model().fit(matrix, target)
    card = _load_model_card()
    validation = ValidationResult(**card["validation"])
    return _Bundle(
        model=model,
        training_fingerprints=tuple(fingerprint(molecule) for molecule in molecules),
        validation=validation,
        model_card=card,
    )


def _tree_standard_deviation(model: Pipeline, vector: np.ndarray) -> float:
    transformed = model.named_steps["impute"].transform(vector.reshape(1, -1))
    transformed = model.named_steps["variance"].transform(transformed)
    forest = model.named_steps["regressor"]
    predictions = np.asarray([tree.predict(transformed)[0] for tree in forest.estimators_])
    return float(np.std(predictions, ddof=0))


def predict_temperature(
    cation_smiles: str,
    *,
    name: str = "prediction",
    anion_smiles: str = PENTAZOLATE_SMILES,
    allow_out_of_domain: bool = False,
) -> PredictionResult:
    cation = parse_cation(cation_smiles)
    warnings = []
    if canonical_smiles(anion_smiles) != canonical_smiles(PENTAZOLATE_SMILES):
        warnings.append("阴离子不是训练域中的五唑阴离子")
    charge = formal_charge(cation)
    if charge != 1:
        warnings.append(f"阳离子形式电荷应为 +1，实际 {charge:+d}")
    unsupported = sorted(elements(cation) - ALLOWED_ELEMENTS)
    if unsupported:
        warnings.append(f"包含训练域外元素: {', '.join(unsupported)}")

    bundle = _bundle()
    query_fingerprint = fingerprint(cation)
    similarity = maximum_similarity(query_fingerprint, bundle.training_fingerprints)
    threshold = float(bundle.model_card["applicability"]["minimum_similarity"])
    if similarity < threshold:
        warnings.append(f"最大 Tanimoto 相似度 {similarity:.3f} 低于阈值 {threshold:.3f}")
    if warnings and not allow_out_of_domain:
        raise ApplicabilityError("; ".join(warnings))

    vector = feature_vector(cation)
    temperature = float(bundle.model.predict(vector.reshape(1, -1))[0])
    half_width = bundle.validation.conformal_half_width_c
    return PredictionResult(
        name=name,
        temperature_c=temperature,
        interval_low_c=temperature - half_width,
        interval_high_c=temperature + half_width,
        tree_std_c=_tree_standard_deviation(bundle.model, vector),
        maximum_tanimoto_similarity=similarity,
        in_domain=not warnings,
        warnings=tuple(warnings),
        model_version=str(bundle.model_card["model_version"]),
        validation=bundle.validation,
    )
