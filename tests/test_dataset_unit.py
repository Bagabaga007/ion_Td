import math

import pytest

import ion_td.dataset as dataset
from ion_td.dataset import TrainingRecord, _validate_records, canonical_smiles, load_training_records

pytestmark = pytest.mark.unit


def record(**changes):
    values = dict(
        identifier="x",
        tdec_c=100.0,
        reference="doi",
        cation_smiles="[NH4+]",
        anion_smiles=dataset.PENTAZOLATE_SMILES,
        salt_smiles="[NH4+].N1=NN=N[N-]1",
    )
    values.update(changes)
    return TrainingRecord(**values)


def test_packaged_training_data_contract():
    records = load_training_records()
    assert len(records) == 36
    assert records[-1].identifier == "salt36"
    assert records[-1].tdec_c == 94.0
    assert len({r.identifier for r in records}) == 36


def test_canonical_smiles_and_record_errors():
    assert canonical_smiles("N1=NN=N[N-]1")
    with pytest.raises(ValueError, match="无效 SMILES"):
        canonical_smiles("not-smiles")
    with pytest.raises(ValueError, match="不能为空"):
        _validate_records([])
    with pytest.raises(ValueError, match="ID 必须唯一"):
        _validate_records([record(), record()])
    with pytest.raises(ValueError, match="有限"):
        _validate_records([record(tdec_c=math.nan)])
    with pytest.raises(ValueError, match="非五唑"):
        _validate_records([record(anion_smiles="[Cl-]")])
    with pytest.raises(ValueError, match="SMILES 无效"):
        _validate_records([record(cation_smiles="invalid")])
    with pytest.raises(ValueError, match="形式电荷"):
        _validate_records([record(cation_smiles="N")])


def test_training_header_mismatch(monkeypatch, tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("wrong\nvalue\n")

    class Resource:
        def joinpath(self, *parts):
            return self

        def open(self, *args, **kwargs):
            return bad.open(*args, **kwargs)

    monkeypatch.setattr(dataset, "files", lambda package: Resource())
    with pytest.raises(ValueError, match="列不匹配"):
        load_training_records()
