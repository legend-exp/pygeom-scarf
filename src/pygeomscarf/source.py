from __future__ import annotations

import numpy as np
import pyg4ometry
from pyg4ometry import geant4


def build_source(
    world_lv: geant4.LogicalVolume,
    radius: float,
    z_pos: float,
    reg: geant4.Registry,
    *,
    source_height: float = 10,
    source_radius: float = 1,
    material: str = "G4_Fe",
) -> geant4.LogicalVolume:
    """Build the source holder and source for the SCARF geometry.

    Parameters
    ----------
    world_lv
        The logical volume of the world, to place the source inside.
    z_pos
        The position of the source in mm.
    radius
        The radial position of the source in mm.
    reg
        The registry to add the source to.
    source_height
        The height of the source in mm.
    source_radius
        The radius of the source in mm.

    """

    source_s = pyg4ometry.geant4.solid.Tubs(
        "source", 0, source_radius, source_height, 0, 2 * np.pi, registry=reg, lunit="mm", nslice=720
    )
    source_l = pyg4ometry.geant4.LogicalVolume(source_s, material, "source", registry=reg)

    # place the source into the holder
    pyg4ometry.geant4.PhysicalVolume(
        [0, 0, 0], [0, radius, z_pos, "mm"], source_l, "source", world_lv, registry=reg
    )

    return reg
