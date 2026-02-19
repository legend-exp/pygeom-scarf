from __future__ import annotations

import os
from pathlib import Path

import pygeomtools.geometry
from dbetto import TextDB

from pygeomscarf.core import construct

public_geom = os.getenv("LEGEND_METADATA", "") == ""


def test_import():
    import pygeomscarf  # noqa: F401


def test_construct(tmp_path):
    # just cryostat
    reg = construct(public_geometry=True)
    assert reg.worldVolume is not None

    # with hpge

    reg = construct(
        config={"hpges": [{"name": "V09999A", "pplus_pos_from_lar_center": 120}]},
        public_geometry=True,
    )
    assert reg.worldVolume is not None
    assert "V09999A" in reg.logicalVolumeDict

    # now with source
    reg = construct(
        config={
            "hpges": [{"name": "V09999A", "pplus_pos_from_lar_center": 120}],
            "source": {"pos_from_lar_center": 150},
        },
        public_geometry=True,
    )
    assert reg.worldVolume is not None
    assert "source" in reg.logicalVolumeDict

    # now with fiber shroud
    reg = construct(
        config={
            "hpges": [{"name": "V09999A", "pplus_pos_from_lar_center": 120}],
            "source": {"pos_from_lar_center": 150},
            "fiber_shroud": {
                "center_pos_from_lar_center": 0,
            },
        },
        public_geometry=True,
    )

    assert reg.worldVolume is not None
    assert "fiber_shroud" in reg.physicalVolumeDict

    pygeomtools.geometry.check_registry_sanity(reg, reg)

    # test the gdml can be written
    pygeomtools.write_pygeom(reg, Path(tmp_path) / "test.gdml")

    db = TextDB(Path(__file__).parent / "configs" / "extra")

    reg = construct(
        config={
            "hpges": [{"name": "bege", "pplus_pos_from_lar_center": 120}],
            "source": {"pos_from_lar_center": 150},
            "fiber_shroud": {
                "center_pos_from_lar_center": 0,
            },
        },
        extra_detectors=db,
        public_geometry=True,
    )

    assert reg.worldVolume is not None

    assert "bege" in reg.physicalVolumeDict

    # test the gdml can be written with extra detectors

    reg = construct(
        config={
            "hpges": [{"name": "bege", "pplus_pos_from_lar_center": 120}],
            "source": {"pos_from_lar_center": 150},
            "fiber_shroud": {
                "mode": "detailed",
                "center_pos_from_lar_center": 0,
            },
        },
        extra_detectors=db,
        public_geometry=True,
    )

    assert "fiber_core" in reg.physicalVolumeDict
