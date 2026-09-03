import pytest

from ion_td.model import predict_temperature

pytestmark = pytest.mark.integration


def test_prediction_is_deterministic_and_self_describing():
    first = predict_temperature("[NH3+]O", name="hydroxylammonium")
    second = predict_temperature("[NH3+]O", name="hydroxylammonium")
    assert first == second
    assert first.in_domain is True
    assert first.maximum_tanimoto_similarity == 1.0
    assert first.interval_low_c < first.temperature_c < first.interval_high_c
    assert first.validation.n == 36
    assert first.model_version == "rdkit-rf-pentazolate-v1"
