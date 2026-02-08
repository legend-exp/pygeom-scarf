from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from pyg4ometry import geant4

plt.rcParams["font.size"] = 12
plt.rcParams["figure.dpi"] = 200

log = logging.getLogger(__name__)

# dimensions taken from SCARF technical drawings

INNER_RADIUS = 696 / 2.0
THICKNESS = 2
UPPER_THICKNESS = 0.5
LOWER_HEIGHT = 1501
UPPER_HEIGHT = 780
SHIFT = (LOWER_HEIGHT + UPPER_HEIGHT) / 2

LAR_FILL_HEIGHT = 680

OUTER_RADIUS = 400
TOTAL_HEIGHT = 150 + THICKNESS + LOWER_HEIGHT + UPPER_HEIGHT

# lead shield dimensions
AIR_GAP = 5
LEAD_THICK = 100


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


def gaseous_argon_profile() -> tuple[list, list]:
    """Extract the profile of the gaseous argon volume.

    The geometry is similar to {func}:`extract_inner_cryostat_profile`
    but slightly shifted to account for the cryostat thickness and the LAr volume.

    Warning
    -------
    For now the gaseous argon fills the gap between the LAr and the inner cryostat.

    Returns
    -------
        list of radii, list of heights
    """
    radius = [
        0,
        INNER_RADIUS + (THICKNESS / 2) - UPPER_THICKNESS / 2 - 0.01,  # lower corner
        INNER_RADIUS + (THICKNESS / 2) - UPPER_THICKNESS / 2 - 0.01,
        0,
    ]

    height = [
        0,
        0,
        LAR_FILL_HEIGHT,  # change in thickness
        LAR_FILL_HEIGHT,  # top corner
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


def cryostat_lid_profile() -> tuple[list, list]:
    """Extract the profile of the cryostat lid.

    The lid is a simple cylinder, so the profile is just two points.
    """

    radius = [0, OUTER_RADIUS + 30, OUTER_RADIUS + 30, 0]
    height = [0, 0, 10, 10]
    return radius, height


def lead_profile() -> tuple[list, list]:
    """Extract the profile of the lead shield.

    The lead shield is a simple cylinder, so the profile is just two points.
    """

    radius = [
        0,
        OUTER_RADIUS + AIR_GAP,  # lower corner
        OUTER_RADIUS + AIR_GAP,  # lower corner
        OUTER_RADIUS + AIR_GAP + LEAD_THICK,  # lower corner
        OUTER_RADIUS + AIR_GAP + LEAD_THICK,  # lower corner
        0,
    ]

    height = [0, 0, TOTAL_HEIGHT + AIR_GAP, TOTAL_HEIGHT + AIR_GAP, -LEAD_THICK, -LEAD_THICK]
    return radius, height


def _construct_polycone(
    name: str, radius: list, height: list, reg: geant4.Registry, color: list, material: str | geant4.material
) -> geant4.LogicalVolume:
    """Construct a generic polycone and make its logical volume."""

    solid = geant4.solid.GenericPolycone(
        name, 0, 2 * np.pi, radius, height, registry=reg, lunit="mm", nslice=720
    )

    log = geant4.LogicalVolume(solid, material, name, registry=reg)
    log.pygeom_color_rgba = color

    return log


def _place_polycone(
    name: str, log: geant4.LogicalVolume, mother: geant4.LogicalVolume, z_pos: float, reg: geant4.Registry
):
    """Place the polcyone (on-axis) into the registry."""

    geant4.PhysicalVolume([0, 0, 0], [0, 0, z_pos, "mm"], log, name, mother, registry=reg)


def plot_profiles(profiles: dict):
    """Plot the profiles of the cryostat volumes.

    Parameters
    ----------
    profiles
        Dictionary of profiles, where the keys are the volume names and the values are dictionaries with keys "radius", "height", "shift" and "kwargs" (the latter containing keyword arguments for the polygon patch).

    """

    _, ax = plt.subplots()

    for name, profile in profiles.items():
        r = profile["radius"]
        z = profile["height"]
        shift = profile["shift"]
        verts = list(zip([*r, r[0]], [z + shift for z in z] + [z[0] + shift], strict=True))
        poly = Polygon(verts, closed=True, label=name, **profile["kwargs"])
        ax.add_patch(poly)

    ax.set_xlim(0, 520)
    ax.set_ylim(-1500, 1500)
    ax.set_xlabel("Radius [mm]")
    ax.set_ylabel("Height [mm]")
    ax.set_title("Profile used for cryostat construction")
    plt.tight_layout()
    plt.show()


def build_cryostat(
    world_log: geant4.LogicalVolume, reg: geant4.Registry, *, plot: bool = False
) -> geant4.Registry:
    """Construct the SCARF cryostat and LAr and add this to the
    geometry.

    .. warning::
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

    profiles = {}

    # inner cryostat
    r_inner, z_inner = inner_cryostat_profile()

    inner = _construct_polycone(
        "inner_cryostat", r_inner, z_inner, reg, color=[0.7, 0.3, 0.3, 0.1], material="G4_Fe"
    )

    _place_polycone("inner_cryostat", inner, world_log, -SHIFT, reg)

    # save the profile
    profiles["inner_cryostat"] = {
        "radius": r_inner,
        "height": z_inner,
        "shift": -SHIFT,
        "kwargs": {"facecolor": "black", "alpha": 1, "edgecolor": "k"},
    }

    # now add the lar
    r_lar, z_lar = lar_profile()

    lar = _construct_polycone("lar", r_lar, z_lar, reg, color=[0, 1, 1, 0.5], material="G4_lAr")
    _place_polycone("lar", lar, inner, THICKNESS, reg)

    profiles["lar"] = {
        "radius": r_lar,
        "height": z_lar,
        "shift": -SHIFT + THICKNESS,
        "kwargs": {"facecolor": "cyan", "alpha": 1},
    }

    # place gaseous argon as a daughter of the inner cryostat, to fill the gap between the LAr and the inner cryostat

    r_gas, z_gas = gaseous_argon_profile()
    gas = _construct_polycone(
        "gaseous_argon", r_gas, z_gas, reg, color=[0.8784, 1.0, 1.0, 1.0], material="G4_Ar"
    )
    _place_polycone("gaseous_argon", gas, lar, LOWER_HEIGHT + UPPER_HEIGHT - LAR_FILL_HEIGHT, reg)

    profiles["gaseous_argon"] = {
        "radius": r_gas,
        "height": z_gas,
        "shift": -SHIFT + LOWER_HEIGHT + UPPER_HEIGHT - LAR_FILL_HEIGHT + THICKNESS,
        "kwargs": {"facecolor": "lightcyan"},
    }

    # add the outer cryostat
    r_outer, z_outer = outer_cryostat_profile()

    outer = _construct_polycone(
        "outer_cryostat", r_outer, z_outer, reg, color=[0.7, 0.3, 0.3, 0.1], material="G4_Fe"
    )
    _place_polycone("outer_cryostat", outer, world_log, -150 - THICKNESS - SHIFT, reg)

    profiles["outer_cryostat"] = {
        "radius": r_outer,
        "height": z_outer,
        "shift": -SHIFT - THICKNESS - 150,
        "kwargs": {"facecolor": "blue", "edgecolor": "darkblue"},
    }

    # add the cryostat lid (for now just a cylinder)

    lid_r, lid_z = cryostat_lid_profile()

    lid = _construct_polycone("cryostat_lid", lid_r, lid_z, reg, color=[0.7, 0.3, 0.3, 0.1], material="G4_Fe")
    z_lid = LOWER_HEIGHT + UPPER_HEIGHT + 3 - SHIFT

    _place_polycone("cryostat_lid", lid, world_log, z_lid, reg)

    profiles["cryostat_lid"] = {
        "radius": lid_r,
        "height": lid_z,
        "shift": z_lid,
        "kwargs": {"facecolor": "blue", "edgecolor": "darkblue"},
    }

    # add the lead
    r_lead, z_lead = lead_profile()

    lead = _construct_polycone(
        "lead_shield", r_lead, z_lead, reg, color=[0.9, 0.9, 0.9, 0.1], material="G4_Pb"
    )
    _place_polycone("lead_shield", lead, world_log, -150 - THICKNESS - AIR_GAP - 2 - SHIFT, reg)

    profiles["lead_shield"] = {
        "radius": r_lead,
        "height": z_lead,
        "shift": -SHIFT - THICKNESS - 150 - AIR_GAP - 2,
        "kwargs": {"facecolor": "gray", "edgecolor": "grey", "alpha": 0.3},
    }

    # now plot if requested
    if plot:
        plot_profiles(profiles)

    return reg
