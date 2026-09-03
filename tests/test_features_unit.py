import numpy as np
import pytest
from rdkit import Chem

import ion_td.features as features

pytestmark = pytest.mark.unit


def test_feature_vector_and_chemistry_helpers():
    molecule = features.parse_cation("[NH3+]O")
    assert features.formal_charge(molecule) == 1
    assert features.elements(molecule) == frozenset({"N", "O"})
    vector = features.feature_vector(molecule)
    assert vector.ndim == 1
    assert len(vector) == len(features.descriptor_functions()) + features.MORGAN_SIZE
    fp = features.fingerprint(molecule)
    assert features.maximum_similarity(fp, [fp]) == 1.0
    with pytest.raises(ValueError, match="无效阳离子"):
        features.parse_cation("bad")
    with pytest.raises(ValueError, match="不能为空"):
        features.maximum_similarity(fp, [])


def test_descriptor_failure_becomes_nan(monkeypatch):
    molecule = Chem.MolFromSmiles("[NH4+]")

    def broken(mol):
        raise ValueError("broken")

    monkeypatch.setattr(features, "descriptor_functions", lambda: (("broken", broken),))
    vector = features.feature_vector(molecule)
    assert np.isnan(vector[0])
