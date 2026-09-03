from types import SimpleNamespace

import numpy as np
import pytest
from rdkit import Chem

import ion_td.model as model
from ion_td.model import ApplicabilityError, _conformal_half_width, predict_temperature

pytestmark = pytest.mark.unit


def test_conformal_validation():
    assert _conformal_half_width(np.array([1.0, 2.0, 3.0]), 0.5) == 2.0
    with pytest.raises(ValueError, match="coverage"):
        _conformal_half_width(np.array([1.0]), 1.0)


def test_domain_rejections_and_override():
    with pytest.raises(ApplicabilityError, match="阴离子"):
        predict_temperature("[NH4+]", anion_smiles="[Cl-]")
    with pytest.raises(ApplicabilityError, match="形式电荷"):
        predict_temperature("N")
    with pytest.raises(ApplicabilityError, match="训练域外元素"):
        predict_temperature("[Na+]")
    result = predict_temperature(
        "[Na+]", anion_smiles="[Cl-]", allow_out_of_domain=True, name="outside"
    )
    assert result.in_domain is False
    assert len(result.warnings) >= 2
    assert result.to_dict()["warnings"] == list(result.warnings)


def test_low_similarity_branch(monkeypatch):
    validation = model.ValidationResult(1, 0.0, 1.0, 1.0, 2.0)
    fake_model = SimpleNamespace(predict=lambda value: np.array([100.0]))
    bundle = SimpleNamespace(
        model=fake_model,
        training_fingerprints=(object(),),
        validation=validation,
        model_card={"applicability": {"minimum_similarity": 0.5}, "model_version": "x"},
    )
    monkeypatch.setattr(model, "_bundle", lambda: bundle)
    monkeypatch.setattr(model, "fingerprint", lambda molecule: object())
    monkeypatch.setattr(model, "maximum_similarity", lambda query, refs: 0.1)
    with pytest.raises(ApplicabilityError, match="Tanimoto"):
        predict_temperature("[NH4+]")


def test_tree_standard_deviation():
    bundle = model._bundle()
    molecule = Chem.MolFromSmiles("[NH4+]")
    vector = model.feature_vector(molecule)
    assert model._tree_standard_deviation(bundle.model, vector) >= 0.0
