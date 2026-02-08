from __future__ import annotations

import os

from pygeomscarf.core import construct

public_geom = os.getenv("LEGEND_METADATA", "") == ""


def test_import():
    import pygeomscarf  # noqa: F401


def test_construct():
    reg = construct(public_geometry=public_geom)
    assert reg.worldVolume is not None
