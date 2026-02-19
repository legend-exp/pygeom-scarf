from __future__ import annotations

from dbetto import AttrsDict

from pygeomscarf.utils import merge_configs


def test_merge_configs():
    base = AttrsDict({"a": 1, "b": 2})
    extra = AttrsDict({"b": 3, "c": 4})

    merged = merge_configs(base, extra)

    assert merged == AttrsDict({"a": 1, "b": 3, "c": 4})

    # test with extra as None
    merged = merge_configs(base, None)
    assert merged == base
