from __future__ import annotations

from pyg4ometry import geant4
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.cavern import construct_cavern


def test_cavern_construction():
    reg = geant4.Registry()
    mat = LegendMaterialRegistry(reg).rock
    world_lv = geant4.LogicalVolume(
        geant4.solid.Box("world_solid", 50000, 50000, 50000, registry=reg), mat, "world_lv", registry=reg
    )

    reg = construct_cavern(
        inner_radius=10000,
        outer_radius=20000,
        reg=reg,
        mat=mat,
        world_lv=world_lv,
    )
    assert "cavern" in reg.logicalVolumeDict
    assert "cavern" in reg.physicalVolumeDict
