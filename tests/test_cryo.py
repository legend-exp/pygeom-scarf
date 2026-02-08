from __future__ import annotations

import numpy as np
import pyg4ometry

from pygeomscarf.cryo import (
    build_cryostat,
    cryostat_lid_profile,
    inner_cryostat_profile,
    lead_profile,
    outer_cryostat_profile,
    plot_profiles
)


def test_build_cryostat():
    reg = pyg4ometry.geant4.Registry()
    world_s = pyg4ometry.geant4.solid.Tubs("World_s", 0, 3000, 5000, 0, 2 * np.pi, registry=reg, lunit="mm")
    world_l = pyg4ometry.geant4.LogicalVolume(world_s, "G4_Galactic", "World", registry=reg)
    reg.setWorld(world_l)

    reg = build_cryostat(world_l, reg, plot=False)

    assert isinstance(reg, pyg4ometry.geant4.Registry)


def test_profiles():
    for prof in [outer_cryostat_profile, cryostat_lid_profile, lead_profile, inner_cryostat_profile]:
        r, z = prof()
        assert isinstance(r, list)
        assert isinstance(z, list)
        assert len(r) == len(z)


def test_plot():
    assert plot_profiles({"cryostat":{"radius": [0, 100, 200], "height": [0, 100, 200],"shift":0,"kwargs":{}}}) is None

