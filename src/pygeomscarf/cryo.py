"""Construction of the SCARF cryostat and LAr.

The geometry is based on the CAD model of the SCARF cryostat, but is simplified to be a generic polycone.

- The inner cryostat is almost cylindrical, with a slight tapering to account for the change in thickness.
- The LAr volume fills the inner cryostat, and there is a gap between the LAr and the inner cryostat that is filled with gaseous argon.
- The outer cryostat is also a simple cylinder, and there is a lead shield surrounding the entire cryostat.

The relevant dimensions are defined in the configuration file, which should have the following format:

.. code-block:: yaml

    inner:
        radius_in_mm: ...
        upper:
            thickness_in_mm: ...
            height_in_mm: ...
        lower:
            thickness_in_mm: ...
            height_in_mm: ...
    outer:
        radius_in_mm: ...
        height_in_mm: ...
        thickness_in_mm: ...
    top:
        height_in_mm: ...
        radius_in_mm: ...
    gas_argon:
        height_in_mm: ...
    lead:
        air_gap_in_mm: ...
        thickness_in_mm: ...
"""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
import pygeomoptics
from dbetto import AttrsDict
from matplotlib.patches import Polygon
from pyg4ometry import geant4
from pygeomtools.materials import LegendMaterialRegistry

from pygeomscarf.utils import _place_pv

plt.rcParams["font.size"] = 12
plt.rcParams["figure.dpi"] = 200

log = logging.getLogger(__name__)

TOL = 0.01  # mm, tolerance to avoid overlaps


def inner_cryostat_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Profile of the inner cryostat. See :func:`construct_inner_cryostat` for
    more details.

    The geometry is constructed as a :class:`pyg4ometry.geant4.solid.genericPolycone`, which
    is almost cylindrical with a slight tapering to account for the change in thickness.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.

    Warning
    -------
    The LAr must be placed as a daughter volume for this to make sense.

    Returns
    -------
        list of radii, list of heights
    """

    inner = cryostat_meta.inner

    radius = [
        0,
        inner.radius_in_mm + inner.lower.thickness_in_mm,  # lower corner
        inner.radius_in_mm + inner.lower.thickness_in_mm,  # change in thickness
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2.0) + (inner.upper.thickness_in_mm / 2.0),
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2) + (inner.upper.thickness_in_mm / 2),
        0,
    ]

    height = [
        0,
        0,  # lower corner
        inner.lower.height_in_mm + inner.lower.thickness_in_mm,  # change in thickness
        inner.lower.height_in_mm + inner.lower.thickness_in_mm,
        inner.lower.height_in_mm + inner.upper.height_in_mm + inner.lower.thickness_in_mm,
        inner.lower.height_in_mm + inner.upper.height_in_mm + inner.lower.thickness_in_mm,  # top corner
    ]
    return radius, height


def lar_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Extract the profile of the lar volume.

    The geometry is similar to :func:`extract_inner_cryostat_profile`
    but slightly shifted to account for the cryostat thickness.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.

    Returns
    -------
        list of radii, list of heights
    """
    inner = cryostat_meta.inner

    radius = [
        0,
        inner.radius_in_mm,  # lower corner
        inner.radius_in_mm,  # change in thickness
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2) - inner.upper.thickness_in_mm / 2,
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2) - inner.upper.thickness_in_mm / 2,  # top,
        0,
    ]

    height = [
        0,
        0,  # lower corner
        inner.lower.height_in_mm,  # change in thickness
        inner.lower.height_in_mm,
        inner.lower.height_in_mm + inner.upper.height_in_mm - TOL,
        inner.lower.height_in_mm + inner.upper.height_in_mm - TOL,  # top corner
    ]
    return radius, height


def gaseous_argon_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Extract the profile of the gaseous argon volume.

    The geometry is similar to :func:`extract_inner_cryostat_profile`
    but slightly shifted to account for the cryostat thickness and the LAr volume.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.

    Returns
    -------
        list of radii, list of heights
    """
    inner = cryostat_meta.inner
    radius = [
        0,
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2) - inner.upper.thickness_in_mm / 2 - TOL,
        inner.radius_in_mm + (inner.lower.thickness_in_mm / 2) - inner.upper.thickness_in_mm / 2 - TOL,
        0,
    ]

    height = [
        0,
        0,
        cryostat_meta.gas_argon.height_in_mm - 2 * TOL,
        cryostat_meta.gas_argon.height_in_mm - 2 * TOL,
    ]
    return radius, height


def outer_cryostat_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Extract the profile of the outer cryostat.

    Defines the profile of the outer cryostat vessel.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.
    """

    outer = cryostat_meta.outer

    radius = [
        0,
        outer.radius_in_mm + outer.thickness_in_mm,
        outer.radius_in_mm + outer.thickness_in_mm,
        outer.radius_in_mm,
        outer.radius_in_mm,
        0,
    ]

    height = [0, 0, outer.height_in_mm, outer.height_in_mm, outer.thickness_in_mm, outer.thickness_in_mm]
    return radius, height


def cryostat_lid_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Extract the profile of the cryostat lid.

    The lid is a simple cylinder, so the profile is just two points.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.

    """
    lid = cryostat_meta.top
    radius = [0, lid.radius_in_mm, lid.radius_in_mm, 0]
    height = [0, 0, lid.height_in_mm, lid.height_in_mm]
    return radius, height


def lead_profile(cryostat_meta: AttrsDict) -> tuple[list, list]:
    """Extract the profile of the lead shield.

    The lead shield is a simple cylinder, so the profile is just two points.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.

    """
    outer = cryostat_meta.outer
    lead = cryostat_meta.lead

    radius = [
        0,
        outer.radius_in_mm + lead.air_gap_in_mm,  # lower corner
        outer.radius_in_mm + lead.air_gap_in_mm,  # lower corner
        outer.radius_in_mm + lead.air_gap_in_mm + lead.thickness_in_mm,  # lower corner
        outer.radius_in_mm + lead.air_gap_in_mm + lead.thickness_in_mm,  # lower corner
        0,
    ]

    height = [
        0,
        0,
        outer.height_in_mm + lead.air_gap_in_mm,
        outer.height_in_mm + lead.air_gap_in_mm,
        -lead.thickness_in_mm,
        -lead.thickness_in_mm,
    ]
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


def set_steel_reflectivity(reg: geant4.Registry, cryostat_name: str, lar_name: str):
    """Set the reflectivity of the inner cryostat.

    Warning
    -------
    For now the reflectivity is set to that of copper, which should be similar.

    Parameters
    ----------
    reg
        The registry containing the logical volumes.
    cryostat_name
        The name of the inner cryostat physical volume volume.
    lar_name
        The name of the lar physical volume volume.

    """
    _to_steel = geant4.solid.OpticalSurface(
        "surface_to_steel",
        finish="ground",
        model="unified",
        surf_type="dielectric_metal",
        value=0.5,
        registry=reg,
    )

    pygeomoptics.copper.pyg4_copper_attach_reflectivity(_to_steel, reg)

    cryostat = reg.physicalVolumeDict[cryostat_name]
    lar = reg.physicalVolumeDict[lar_name]

    geant4.BorderSurface("bsurface_lar_cryostat", lar, cryostat, _to_steel, reg)
    geant4.BorderSurface("bsurface_cryostat_lar", cryostat, lar, _to_steel, reg)

    return reg


def build_cryostat(
    cryostat_meta: AttrsDict,
    world_log: geant4.LogicalVolume,
    reg: geant4.Registry,
    mats: LegendMaterialRegistry,
    *,
    plot: bool = False,
) -> tuple[geant4.Registry, float, float]:
    """Construct the SCARF cryostat and LAr and add this to the
    geometry.

    .. warning::
        The geometry for the lower part of the cryostat and the
        lid is approximate.

    Parameters
    ----------
    cryostat_meta
        The metadata containing the relevant dimensions of the cryostat, see :mod:`pygeomscarf.cryo` for more details.
    world_log
        The logical volume of the world.
    reg
        The registry to add the cryostat to.
    plot
        Flag to plot the profile of the cryostat volumes.
    """

    profiles = {}

    # inner cryostat
    r_inner, z_inner = inner_cryostat_profile(cryostat_meta)

    inner = _construct_polycone(
        "inner_cryostat", r_inner, z_inner, reg, color=[0.7, 0.3, 0.3, 0.1], material=mats.metal_steel
    )
    shift = (cryostat_meta.inner.lower.height_in_mm + cryostat_meta.inner.upper.height_in_mm) / 2.0

    _place_pv("inner_cryostat", inner, world_log, z_pos=-shift, reg=reg)

    # save the profile
    profiles["inner_cryostat"] = {
        "radius": r_inner,
        "height": z_inner,
        "shift": -shift,
        "kwargs": {"facecolor": "black", "alpha": 1, "edgecolor": "k"},
    }

    # now add the lar
    r_lar, z_lar = lar_profile(cryostat_meta)

    lar = _construct_polycone("lar", r_lar, z_lar, reg, color=[0, 1, 1, 0.5], material=mats.liquidargon)
    _place_pv("lar", lar, inner, z_pos=cryostat_meta.inner.lower.thickness_in_mm, reg=reg)

    profiles["lar"] = {
        "radius": r_lar,
        "height": z_lar,
        "shift": -shift + cryostat_meta.inner.lower.thickness_in_mm,
        "kwargs": {"facecolor": "cyan", "alpha": 1},
    }

    reg = set_steel_reflectivity(reg, "lar", "inner_cryostat")

    # place gaseous argon as a daughter of the inner cryostat, to fill the gap between the LAr and the inner cryostat

    r_gas, z_gas = gaseous_argon_profile(cryostat_meta)
    gas = _construct_polycone(
        "gaseous_argon", r_gas, z_gas, reg, color=[0.8784, 1.0, 1.0, 1.0], material="G4_Ar"
    )
    _place_pv(
        "gaseous_argon",
        gas,
        lar,
        z_pos=cryostat_meta.inner.lower.height_in_mm
        + cryostat_meta.inner.upper.height_in_mm
        - cryostat_meta.gas_argon.height_in_mm,
        reg=reg,
    )

    profiles["gaseous_argon"] = {
        "radius": r_gas,
        "height": z_gas,
        "shift": -shift
        + cryostat_meta.inner.lower.height_in_mm
        + cryostat_meta.inner.upper.height_in_mm
        - cryostat_meta.gas_argon.height_in_mm,
        "kwargs": {"facecolor": "lightcyan"},
    }

    # add the outer cryostat
    r_outer, z_outer = outer_cryostat_profile(cryostat_meta)

    outer = _construct_polycone(
        "outer_cryostat", r_outer, z_outer, reg, color=[0.7, 0.3, 0.3, 0.1], material=mats.metal_steel
    )
    _place_pv(
        "outer_cryostat",
        outer,
        world_log,
        z_pos=-150 - cryostat_meta.inner.lower.thickness_in_mm - shift,
        reg=reg,
    )

    profiles["outer_cryostat"] = {
        "radius": r_outer,
        "height": z_outer,
        "shift": -shift - cryostat_meta.inner.lower.thickness_in_mm - 150,
        "kwargs": {"facecolor": "blue", "edgecolor": "darkblue"},
    }

    # add the cryostat lid (for now just a cylinder)
    lid_r, lid_z = cryostat_lid_profile(cryostat_meta)

    lid = _construct_polycone(
        "cryostat_lid", lid_r, lid_z, reg, color=[0.7, 0.3, 0.3, 0.1], material=mats.metal_steel
    )
    z_lid = cryostat_meta.inner.lower.height_in_mm + cryostat_meta.inner.upper.height_in_mm + 3 - shift

    _place_pv("cryostat_lid", lid, world_log, z_pos=z_lid, reg=reg)

    profiles["cryostat_lid"] = {
        "radius": lid_r,
        "height": lid_z,
        "shift": z_lid,
        "kwargs": {"facecolor": "blue", "edgecolor": "darkblue"},
    }

    # add the lead
    r_lead, z_lead = lead_profile(cryostat_meta)

    lead = _construct_polycone(
        "lead_shield", r_lead, z_lead, reg, color=[0.9, 0.9, 0.9, 0.1], material="G4_Pb"
    )
    _place_pv(
        "lead_shield",
        lead,
        world_log,
        z_pos=-150 - 2 * cryostat_meta.outer.thickness_in_mm - cryostat_meta.lead.air_gap_in_mm - shift,
        reg=reg,
    )

    profiles["lead_shield"] = {
        "radius": r_lead,
        "height": z_lead,
        "shift": -150 - cryostat_meta.outer.thickness_in_mm - cryostat_meta.lead.air_gap_in_mm - shift,
        "kwargs": {"facecolor": "gray", "edgecolor": "grey", "alpha": 0.3},
    }

    # now plot if requested
    if plot:
        plot_profiles(profiles)
        plt.show()

    return reg
