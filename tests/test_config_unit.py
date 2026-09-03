import pytest

from ion_td.config import PredictionConfig, load_config
from ion_td.dataset import PENTAZOLATE_SMILES

pytestmark = pytest.mark.unit


def test_flat_and_nested_config(tmp_path):
    flat = PredictionConfig.from_mapping({"name": "x", "cation_smiles": "[NH4+]"})
    assert flat.anion_smiles == PENTAZOLATE_SMILES
    nested_file = tmp_path / "config.yaml"
    nested_file.write_text(
        "name: y\nSMILES:\n  cation: '[NH3+]O'\n  anion: null\nallow_out_of_domain: true\n"
    )
    nested = load_config(str(nested_file))
    assert nested.name == "y" and nested.allow_out_of_domain is True
    assert nested.anion_smiles == PENTAZOLATE_SMILES


def test_config_errors(tmp_path):
    with pytest.raises(ValueError, match="必须提供"):
        PredictionConfig.from_mapping({})
    bad = tmp_path / "bad.yaml"
    bad.write_text("- list\n")
    with pytest.raises(ValueError, match="根节点"):
        load_config(str(bad))
