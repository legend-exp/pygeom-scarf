from __future__ import annotations

from importlib import resources

import dbetto
import numpy as np
import pyg4ometry
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.cryo import (
    build_cryostat,
    cryostat_lid_profile,
    inner_cryostat_profile,
    lead_profile,
    outer_cryostat_profile,
    plot_profiles,
)


def test_build_cryostat():
    reg = pyg4ometry.geant4.Registry()
    mats = LegendMaterialRegistry(reg)
    world_s = pyg4ometry.geant4.solid.Tubs("World_s", 0, 3000, 5000, 0, 2 * np.pi, registry=reg, lunit="mm")
    world_l = pyg4ometry.geant4.LogicalVolume(world_s, "G4_Galactic", "World", registry=reg)
    reg.setWorld(world_l)

    cryostat_meta = dbetto.AttrsDict(
        dbetto.utils.load_dict(resources.files("pygeomscarf") / "configs" / "cryostat.yaml")
    )

    reg = build_cryostat(cryostat_meta, world_l, reg, mats, plot=False)

    assert isinstance(reg, pyg4ometry.geant4.Registry)

    assert set(reg.surfaceDict.keys()) == {"bsurface_lar_cryostat", "bsurface_cryostat_lar"}


def test_profiles():
    cryostat_meta = dbetto.AttrsDict(
        dbetto.utils.load_dict(resources.files("pygeomscarf") / "configs" / "cryostat.yaml")
    )

    for prof in [outer_cryostat_profile, cryostat_lid_profile, lead_profile, inner_cryostat_profile]:
        r, z = prof(cryostat_meta)
        assert isinstance(r, list)
        assert isinstance(z, list)
        assert len(r) == len(z)


def test_plot():
    assert (
        plot_profiles(
            {"cryostat": {"radius": [0, 100, 200], "height": [0, 100, 200], "shift": 0, "kwargs": {}}}
        )
        is None
    )
