from __future__ import annotations

import os

from pygeomscarf.core import construct

public_geom = os.getenv("LEGEND_METADATA", "") == ""


def test_import():
    import pygeomscarf  # noqa: F401


def test_construct():
    # just cryostat
    reg = construct(public_geometry=public_geom)
    assert reg.worldVolume is not None

    # with hpge

    reg = construct(
        config={"hpges": [{"name": "V09999A", "pplus_pos_from_lar_center": 120}]},
        public_geometry=public_geom,
    )
    assert reg.worldVolume is not None
    assert "V09999A" in reg.logicalVolumeDict
