"""强制每个测试归属于且仅归属于一个主层。"""

import pytest

LAYERS = ("unit", "integration", "config", "system")


def pytest_collection_modifyitems(items):
    invalid = []
    for item in items:
        found = [name for name in LAYERS if item.get_closest_marker(name)]
        if len(found) != 1:
            invalid.append(f"{item.nodeid}: {found or 'missing'}")
    if invalid:
        raise pytest.UsageError("测试必须且只能属于一个主层:\n" + "\n".join(invalid))
