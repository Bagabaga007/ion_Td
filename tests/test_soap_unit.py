import numpy as np
import pytest
import builtins

import ion_td.soap as soap

pytestmark = pytest.mark.unit


def test_read_xyz_and_molecular_soap(tmp_path):
    xyz = tmp_path / "water.xyz"
    xyz.write_text("3\nwater\nO 0 0 0\nH 0 0 1\nH 0 1 0\n")
    symbols, positions = soap.read_xyz(str(xyz))
    assert symbols == ["O", "H", "H"] and positions.shape == (3, 3)
    assert soap.molecular_soap(str(xyz)).shape == (3696,)


def test_xyz_errors(tmp_path):
    short = tmp_path / "short.xyz"
    short.write_text("1\ncomment\n")
    with pytest.raises(ValueError, match="内容不足"):
        soap.read_xyz(str(short))
    bad_count = tmp_path / "bad_count.xyz"
    bad_count.write_text("x\ncomment\nH 0 0 0\n")
    with pytest.raises(ValueError, match="首行"):
        soap.read_xyz(str(bad_count))
    incomplete = tmp_path / "incomplete.xyz"
    incomplete.write_text("2\ncomment\nH 0 0 0\nH 0 0\n")
    with pytest.raises(ValueError, match="实际读取"):
        soap.read_xyz(str(incomplete))
    unsupported = tmp_path / "unsupported.xyz"
    unsupported.write_text("1\ncomment\nF 0 0 0\n")
    with pytest.raises(ValueError, match="不支持元素"):
        soap.read_xyz(str(unsupported))


def test_soap_dimension_guard(monkeypatch, tmp_path):
    xyz = tmp_path / "h.xyz"
    xyz.write_text("1\nh\nH 0 0 0\n")

    class FakeSOAP:
        def __init__(self, **kwargs):
            pass

        def create(self, atoms):
            return np.zeros(2)

    import dscribe.descriptors

    monkeypatch.setattr(dscribe.descriptors, "SOAP", FakeSOAP)
    with pytest.raises(ValueError, match="维度异常"):
        soap.molecular_soap(str(xyz))


def test_soap_missing_optional_dependency(monkeypatch, tmp_path):
    xyz = tmp_path / "h.xyz"
    xyz.write_text("1\nh\nH 0 0 0\n")
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "dscribe.descriptors":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(ImportError, match=r"ion-td\[geometry\]"):
        soap.molecular_soap(str(xyz))
