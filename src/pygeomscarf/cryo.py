from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from pyg4ometry import geant4
import matplotlib.colors as mcolors
plt.rcParams["font.size"]=12
plt.rcParams["figure.dpi"]=200

log = logging.getLogger(__name__)

# dimensions taken from SCARF technical drawings

INNER_RADIUS = 696 / 2.0
THICKNESS = 2
UPPER_THICKNESS = 0.5
LOWER_HEIGHT = 1501
UPPER_HEIGHT = 780
SHIFT = (LOWER_HEIGHT + UPPER_HEIGHT) / 2

OUTER_RADIUS = 400
TOTAL_HEIGHT = 150 + THICKNESS + LOWER_HEIGHT + UPPER_HEIGHT


def inner_cryostat_profile() -> tuple[list, list]:
    """Profile of the inner cryostat. See {func}`construct_inner_cryostat` for
    more details.

    The geometry is constructed as a {class}`pyg4ometry.geant4.solid.genericPolcyone`, which
    is almost cylindrical with a slight tapering to account for the change in thickness.

    Warning
    -------
    The LAr must be placed as a daughter volume for this to make sense.

    Returns
    -------
        list of radii, list of heights
    """
    radius = [
        0,
        INNER_RADIUS + THICKNESS,  # lower corner
        INNER_RADIUS + THICKNESS,  # change in thickness
        INNER_RADIUS + (THICKNESS / 2) + UPPER_THICKNESS / 2,
        INNER_RADIUS + (THICKNESS / 2) + UPPER_THICKNESS / 2,  # top,
        0,
    ]

    height = [
        0,
        0,  # lower corner
        LOWER_HEIGHT + THICKNESS,  # change in thickness
        LOWER_HEIGHT + THICKNESS,
        LOWER_HEIGHT + UPPER_HEIGHT + THICKNESS,
        LOWER_HEIGHT + UPPER_HEIGHT + THICKNESS,  # top corner
    ]
    return radius, height


def lar_profile() -> tuple[list, list]:
    """Extract the profile of the lar volume.

    The geometry is similar to {func}:`extract_inner_cryostat_profile`
    but slightly shifted to account for the cryostat thickness.

    Warning
    -------
    For now the LAr fills the entire cryostat.

    Returns
    -------
        list of radii, list of heights
    """
    radius = [
        0,
        INNER_RADIUS,  # lower corner
        INNER_RADIUS,  # change in thickness
        INNER_RADIUS + (THICKNESS / 2) - UPPER_THICKNESS / 2,
        INNER_RADIUS + (THICKNESS / 2) - UPPER_THICKNESS / 2,  # top,
        0,
    ]

    height = [
        0,
        0,  # lower corner
        LOWER_HEIGHT,  # change in thickness
        LOWER_HEIGHT,
        LOWER_HEIGHT + UPPER_HEIGHT,
        LOWER_HEIGHT + UPPER_HEIGHT,  # top corner
    ]
    return radius, height


def outer_cryostat_profile() -> tuple[list, list]:
    """Extract the profile of the outer cryostat.

    Defines the profile of the outer cryostat vessel.
    """

    radius = [
        0,
        OUTER_RADIUS + THICKNESS,  # lower corner
        OUTER_RADIUS + THICKNESS,  # change in thickness
        OUTER_RADIUS,
        OUTER_RADIUS,
        0,
    ]

    height = [0, 0, TOTAL_HEIGHT, TOTAL_HEIGHT, THICKNESS, THICKNESS]
    return radius, height

def _construct_polycone(
    name: str, radius: list, height: list, reg: geant4.Registry, color: list, material: str | geant4.material
) -> geant4.LogicalVolume:
    """Construct a generic polycone and make its logical volume."""

    print(radius, height)
    solid = geant4.solid.GenericPolycone(
        name, 0, 2 * np.pi, radius, height, registry=reg, lunit="mm", nslice=720
    )
    print(solid)
    log = geant4.LogicalVolume(solid, material, name, registry=reg)
    log.pygeom_color_rgba = [0.7, 0.3, 0.3, 0.3]

    return log


def _place_polycone(
    name: str, log: geant4.LogicalVolume, mother: geant4.LogicalVolume, z_pos: float, reg: geant4.Registry
):
    """Place the polcyone (on-axis) into the registry."""

    geant4.PhysicalVolume([0, 0, 0], [0, 0, z_pos, "mm"], log, name, mother, registry=reg)


def build_cryostat(
    world_log: geant4.LogicalVolume, reg: geant4.Registry, *, plot: bool = False
) -> geant4.Registry:
    """Construct the SCARF cryostat and LAr and add this to the
    geometry.

    ... warning
        The geometry for the lower part of the cryostat and the
        lid is approximate.

    Parameters
    ----------
    world_log
        The logical volume of the world.
    reg
        The registry to add the cryostat to.
    plot
        Flag to plot the profile of the cryostat volumes.
    """

    if plot:
        fig, ax = plt.subplots(figsize=(4, 8))

    # inner cryostat
    r_inner, z_inner = inner_cryostat_profile()

    inner = _construct_polycone(
        "inner_cryostat", r_inner, z_inner, reg, color=[0.7, 0.3, 0.3, 0.3], material="G4_Fe"
    )

    _place_polycone("inner_cryostat", inner, world_log, -SHIFT,reg )

    if plot:
        verts = list(zip(r_inner + [r_inner[0]], [z - SHIFT for z in z_inner] + [z_inner[0]-SHIFT], strict=True))
        poly = Polygon(verts, closed=True, facecolor = "black",alpha=1, edgecolor="k")
        ax.add_patch(poly,label = "Cryostat")

    # now add the lar
    r_lar, z_lar = lar_profile()

    lar = _construct_polycone(
        "lar", r_lar,z_lar, reg, color=[0, 0.2, 0.8, 0.3], material="G4_lAr"
    )
    _place_polycone("lar", lar, inner, THICKNESS,reg )

    if plot:
        verts = list(zip(r_lar + [r_lar[0]], [z - SHIFT + THICKNESS for z in z_lar] + [z_lar[0]-SHIFT + THICKNESS], strict=True))
        poly = Polygon(verts, closed=True,facecolor="whitesmoke")
        ax.add_patch(poly,label = "LAr")

    r_outer, z_outer = outer_cryostat_profile()

    outer = _construct_polycone(
        "outer_cryostat", r_inner, z_inner, reg, color=[0.7, 0.3, 0.3, 0.3], material="G4_Fe"
    )
    _place_polycone("outer_cryostat", outer, world_log, -150 - THICKNESS - SHIFT,reg )

    if plot:
        verts = list(zip(r_outer + [r_outer[0]], [z -150 - THICKNESS - SHIFT for z in z_outer] + [z_outer[0]-150 - THICKNESS - SHIFT], strict=True))
        poly = Polygon(verts, closed=True,facecolor="black",edgecolor="k")
        ax.add_patch(poly)

        ax.set_xlim(0,500)
        ax.set_ylim(-1500,1500)
        ax.set_xlabel("Radius [mm]")
        ax.set_ylabel("Height [mm]")
        plt.legend()
        plt.tight_layout()
        plt.show()

    return reg