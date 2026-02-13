from __future__ import annotations

import numpy as np
from pyg4ometry import geant4


def construct_cavern(
    inner_radius: float,
    outer_radius,
    reg: geant4.Registry,
    mat: geant4.Material,
    world_lv: geant4.LogicalVolume,
) -> geant4.Registry:
    """Construct the cavern geometry and place it in the world volume.

    Warning
    -------
    The cavern implementation is very simplified only consisting of an upper hemisphere representing the hill
    and a lower cylinder representing the ground.

    Parameters
    ----------
    inner_radius
        The inner radius of the upper hemisphere in mm.
    outer_radius
        The outer radius of the upper hemisphere in mm.
    reg
        The registry to use for the geometry construction.
    world_lv
        The world logical volume to place the cavern in.

    """

    upper_cavern = geant4.solid.Sphere(
        "upper_cavern",
        pRmin=inner_radius,
        pRmax=outer_radius,
        pSPhi=0,
        pDPhi=2 * np.pi,
        pSTheta=0,
        pDTheta=np.pi / 2.0,
        nslice=720,
        nstack=180,
        registry=reg,
        lunit="mm",
    )
    lower_cavern1 = geant4.solid.Tubs(
        "lowercavern1",
        pRMin=0,
        pRMax=outer_radius,
        pDz=10000,
        pSPhi=0,
        pDPhi=2 * np.pi,
        registry=reg,
        lunit="mm",
    )
    lower_cavern2 = geant4.solid.Tubs(
        "lowercavern2", pRMin=0, pRMax=1000, pDz=4000, pSPhi=0, pDPhi=2 * np.pi, registry=reg, lunit="mm"
    )

    lower_cavern = geant4.solid.Subtraction(
        "lower_cavern", lower_cavern1, lower_cavern2, tra2=[[0, 0, 0], [0, 0, 3, "m"]], registry=reg
    )

    cavern = geant4.solid.Union(
        "cavern", upper_cavern, lower_cavern, tra2=[[0, 0, 0], [0, 0, -5, "m"]], registry=reg
    )

    cavern_lv = geant4.LogicalVolume(cavern, mat, "cavern", registry=reg)

    cavern_lv.pygeom_color_rgba = [0.5, 0.5, 0.5, 0.1]

    geant4.PhysicalVolume([0, 0, 0], [0, 0, 1.5, "m"], cavern_lv, "cavern", world_lv, reg)

    return reg
